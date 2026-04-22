#!/usr/bin/env python3
"""Real-time file watcher with async indexing.

Watches configured scan paths and automatically indexes new/modified files.
Integrates with WebSocket for real-time notifications.

Usage:
    python3 file_watcher.py [--paths PATH1,PATH2] [--recursive]
"""

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Set, Optional
from datetime import datetime
from dataclasses import dataclass

import httpx
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
)

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASS,
    EMBED_MODEL,
    TEXT_PREVIEW_LEN,
    MAX_EMBED_TEXT,
    SCAN_PATHS,
    SKIP_DIRS,
)
import gemini_client

# Try to import from existing modules
try:
    from db import init_pool, close_pool, get_conn

    HAS_DB_POOL = True
except ImportError:
    HAS_DB_POOL = False
    import asyncpg


@dataclass
class FileEvent:
    """Represents a file system event."""

    path: str
    event_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime


class AsyncFileIndexer:
    """Async file indexer that processes files from a queue."""

    def __init__(self, queue: asyncio.Queue, model: str = EMBED_MODEL):
        self.queue = queue
        self.model = model
        self.processing = False
        self.stats = {"processed": 0, "failed": 0, "skipped": 0}

    def sha256_file(self, filepath: str) -> str:
        """Compute SHA256 hash of file contents."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""

    def read_preview(self, filepath: str) -> str:
        """Read text preview from file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(TEXT_PREVIEW_LEN)
        except Exception:
            return ""

    async def get_embedding(
        self, client: httpx.AsyncClient, text: str
    ) -> Optional[list]:
        """Get embedding from Gemini."""
        try:
            truncated = text[:MAX_EMBED_TEXT] if text else ""
            return await gemini_client.get_single_embedding(truncated)
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    async def process_file(self, conn, client: httpx.AsyncClient, event: FileEvent):
        """Process a single file event."""
        path = Path(event.path)

        if not path.exists():
            # File deleted
            if event.event_type == "deleted":
                await conn.execute(
                    """
                    UPDATE files 
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || '{"deleted": true}'::jsonb
                    WHERE path = $1
                    """,
                    str(path),
                )
                print(f"  [DELETED] {path.name}")
            return

        # Skip directories
        if path.is_dir():
            return

        # Skip unwanted dirs
        if any(skip in str(path) for skip in SKIP_DIRS):
            self.stats["skipped"] += 1
            return

        # Get file info
        stat = path.stat()
        sha256 = self.sha256_file(str(path))
        preview = self.read_preview(str(path))

        # Check if file already exists
        existing = await conn.fetchrow(
            "SELECT id, sha256 FROM files WHERE path = $1", str(path)
        )

        if existing:
            # Update existing
            if existing["sha256"] != sha256:
                # Content changed - regenerate embedding
                embedding = await self.get_embedding(client, preview)

                await conn.execute(
                    """
                    UPDATE files 
                    SET name = $1, extension = $2, size = $3, 
                        modified = $4, sha256 = $5, content_preview = $6,
                        metadata = metadata - 'deleted'
                    WHERE path = $7
                    """,
                    path.name,
                    path.suffix.lower(),
                    stat.st_size,
                    datetime.fromtimestamp(stat.st_mtime),
                    sha256,
                    preview,
                    str(path),
                )

                if embedding:
                    await conn.execute(
                        """
                        UPDATE file_embeddings 
                        SET embedding = $1::vector, model = $2, created_at = NOW()
                        WHERE file_id = (SELECT id FROM files WHERE path = $3)
                        """,
                        str(embedding),
                        self.model,
                        str(path),
                    )

                print(f"  [UPDATED] {path.name}")
                self.stats["processed"] += 1
            else:
                print(f"  [UNCHANGED] {path.name}")
        else:
            # Insert new file
            file_id = await conn.fetchval(
                """
                INSERT INTO files (path, name, extension, size, created, modified, sha256, content_preview)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                str(path),
                path.name,
                path.suffix.lower(),
                stat.st_size,
                datetime.fromtimestamp(stat.st_ctime),
                datetime.fromtimestamp(stat.st_mtime),
                sha256,
                preview,
            )

            # Generate embedding
            embedding = await self.get_embedding(client, preview)
            if embedding:
                await conn.execute(
                    """
                    INSERT INTO file_embeddings (file_id, embedding, model)
                    VALUES ($1, $2::vector, $3)
                    """,
                    file_id,
                    str(embedding),
                    self.model,
                )

            print(f"  [NEW] {path.name}")
            self.stats["processed"] += 1

    async def run(self):
        """Main processing loop."""
        self.processing = True

        # Connect to database
        if HAS_DB_POOL:
            await init_pool(min_size=1, max_size=2)
            conn_ctx = get_conn()
        else:
            conn = await asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
            conn_ctx = None

        async with httpx.AsyncClient() as client:
            try:
                while self.processing:
                    try:
                        # Get event from queue (with timeout)
                        event = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                        # Use pooled connection or direct
                        if HAS_DB_POOL:
                            async with conn_ctx as conn:
                                await self.process_file(conn, client, event)
                        else:
                            await self.process_file(conn, client, event)

                        self.queue.task_done()

                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        self.stats["failed"] += 1

            finally:
                if HAS_DB_POOL:
                    await close_pool()
                else:
                    await conn.close()

    def stop(self):
        """Stop the indexer."""
        self.processing = False


class FileEventHandler(FileSystemEventHandler):
    """Watchdog event handler that queues file events."""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.seen_paths: Set[str] = set()

    def on_created(self, event):
        if not event.is_directory:
            self._queue_event(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._queue_event(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            self._queue_event(event.src_path, "deleted")

    def _queue_event(self, path: str, event_type: str):
        """Queue a file event for async processing."""
        # Deduplicate rapid events
        key = f"{path}:{event_type}"
        if key in self.seen_paths:
            return

        self.seen_paths.add(key)

        # Create event
        event = FileEvent(path=path, event_type=event_type, timestamp=datetime.now())

        # Add to queue (non-blocking)
        try:
            asyncio.get_event_loop().call_soon_threadsafe(self.queue.put_nowait, event)
            print(f"[{event_type.upper()}] {Path(path).name}")
        except Exception as e:
            print(f"Queue error: {e}")

        # Clear dedup after delay
        asyncio.get_event_loop().call_later(5.0, lambda: self.seen_paths.discard(key))


class FileWatcher:
    """Main file watcher that coordinates observer and indexer."""

    def __init__(self, paths: Optional[list] = None, recursive: bool = True):
        self.paths = paths or list(SCAN_PATHS.keys())
        self.recursive = recursive
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.indexer = AsyncFileIndexer(self.queue)
        self.observer = Observer()
        self.handler = FileEventHandler(self.queue)
        self.running = False

    def start(self):
        """Start watching and indexing."""
        print(f"File Watcher Starting...")
        print(f"Watching paths: {self.paths}")
        print(f"Recursive: {self.recursive}")
        print("-" * 60)

        # Schedule watchers for each path
        for path in self.paths:
            if os.path.exists(path):
                self.observer.schedule(self.handler, path, recursive=self.recursive)
                print(f"  Watching: {path}")
            else:
                print(f"  [SKIP] Path not found: {path}")

        # Start observer in background thread
        self.observer.start()
        self.running = True

        print("-" * 60)
        print("File watcher running. Press Ctrl+C to stop.")

    def stop(self):
        """Stop watching and indexing."""
        self.running = False
        self.indexer.stop()
        self.observer.stop()
        self.observer.join()

        print("\nFile watcher stopped.")
        print(f"Stats: {self.indexer.stats}")

    async def run(self):
        """Run the file watcher."""
        self.start()

        try:
            # Run indexer in background
            await self.indexer.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Real-time file watcher")
    parser.add_argument(
        "--paths", help="Comma-separated paths to watch (default: from config)"
    )
    parser.add_argument(
        "--no-recursive", action="store_true", help="Don't watch subdirectories"
    )

    args = parser.parse_args()

    paths = args.paths.split(",") if args.paths else None
    recursive = not args.no_recursive

    watcher = FileWatcher(paths=paths, recursive=recursive)

    try:
        asyncio.run(watcher.run())
    except KeyboardInterrupt:
        watcher.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
