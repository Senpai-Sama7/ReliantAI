#!/usr/bin/env python3
"""Incremental re-indexing pipeline for embedding model upgrades.

Usage:
    python3 reindexer.py [--model MODEL] [--batch-size N] [--limit N]
    python3 reindexer.py --status

Examples:
    # Re-index 100 files with new model
    python3 reindexer.py --model mxbai-embed-large --limit 100

    # Re-index all missing files in batches of 50
    python3 reindexer.py --model nomic-embed-text --batch-size 50

    # Check re-indexing status
    python3 reindexer.py --status
"""

import asyncio
import argparse
import json
import sys
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

import asyncpg
import httpx

from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASS,
    BATCH_SIZE,
    MAX_EMBED_TEXT,
)
import gemini_client


@dataclass
class ReindexStatus:
    """Status of re-indexing operation."""

    total_files: int
    indexed_with_model: int
    missing_embeddings: int
    percent_complete: float
    current_model: str
    last_updated: str


@dataclass
class ReindexProgress:
    """Progress tracking for ongoing re-index."""

    batch_number: int
    files_processed: int
    files_success: int
    files_failed: int
    avg_time_per_file_ms: float
    eta_seconds: int


async def get_reindex_status(conn: asyncpg.Connection, model: str) -> ReindexStatus:
    """Get current re-indexing status for a model."""

    # Total files
    total = await conn.fetchval("SELECT COUNT(*) FROM files")

    # Files indexed with this model
    indexed = await conn.fetchval(
        """
        SELECT COUNT(DISTINCT fe.file_id) 
        FROM file_embeddings fe 
        WHERE fe.model = $1
        """,
        model,
    )

    # Files missing this model's embeddings
    missing = total - indexed

    percent = (indexed / total * 100) if total > 0 else 0.0

    return ReindexStatus(
        total_files=total,
        indexed_with_model=indexed,
        missing_embeddings=missing,
        percent_complete=percent,
        current_model=model,
        last_updated=datetime.now().isoformat(),
    )


async def get_files_to_reindex(
    conn: asyncpg.Connection, model: str, limit: Optional[int] = None
) -> List[Dict]:
    """Get files that need re-indexing with the specified model."""

    query = """
        SELECT f.id, f.name, f.path, f.extension, f.content_preview, f.updated_at
        FROM files f
        LEFT JOIN file_embeddings fe ON f.id = fe.file_id AND fe.model = $1
        WHERE fe.file_id IS NULL
        ORDER BY f.updated_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = await conn.fetch(query, model)
    return [dict(row) for row in rows]


async def generate_embeddings_batch(
    client: httpx.AsyncClient, model: str, texts: List[str]
) -> Tuple[List[List[float]], float]:
    """Generate embeddings for a batch of texts.

    Returns:
        (embeddings list, time elapsed in ms)
    """
    start = time.perf_counter()

    # Truncate texts to MAX_EMBED_TEXT chars
    truncated = [t[:MAX_EMBED_TEXT] if t else "" for t in texts]

    embeddings = await gemini_client.get_embeddings(truncated)

    elapsed = (time.perf_counter() - start) * 1000

    # Filter out None values
    valid_embeddings = [emb if emb else [0.0] * 768 for emb in embeddings]

    return valid_embeddings, elapsed


async def upsert_embeddings(
    conn: asyncpg.Connection,
    file_ids: List[int],
    embeddings: List[List[float]],
    model: str,
) -> int:
    """Upsert embeddings into database.

    Note: Current schema has unique constraint on file_id only (single model per file).
    This updates the existing embedding and model for each file.

    Returns number of rows inserted/updated.
    """
    count = 0

    for fid, emb in zip(file_ids, embeddings):
        # Check if embedding exists
        existing = await conn.fetchval(
            "SELECT id FROM file_embeddings WHERE file_id = $1", fid
        )

        if existing:
            # Update existing
            await conn.execute(
                """
                UPDATE file_embeddings 
                SET embedding = $1::vector, model = $2, created_at = NOW()
                WHERE file_id = $3
                """,
                str(emb),
                model,
                fid,
            )
        else:
            # Insert new
            await conn.execute(
                """
                INSERT INTO file_embeddings (file_id, embedding, model)
                VALUES ($1, $2::vector, $3)
                """,
                fid,
                str(emb),
                model,
            )

        count += 1

    return count


async def reindex_batch(
    conn: asyncpg.Connection, client: httpx.AsyncClient, model: str, files: List[Dict]
) -> Tuple[int, int, float]:
    """Re-index a batch of files.

    Returns:
        (success_count, fail_count, time_ms)
    """
    if not files:
        return 0, 0, 0.0

    # Extract texts
    texts = []
    file_ids = []

    for f in files:
        content = f.get("content_preview") or ""
        texts.append(content)
        file_ids.append(f["id"])

    try:
        # Generate embeddings
        embeddings, embed_time = await generate_embeddings_batch(client, model, texts)

        if len(embeddings) != len(file_ids):
            raise Exception(
                f"Embedding count mismatch: {len(embeddings)} != {len(file_ids)}"
            )

        # Upsert to database
        await upsert_embeddings(conn, file_ids, embeddings, model)

        return len(file_ids), 0, embed_time

    except Exception as e:
        print(f"  Batch error: {e}")
        return 0, len(file_ids), 0.0


async def run_reindex(
    model: str, batch_size: int = 32, limit: Optional[int] = None, dry_run: bool = False
) -> Dict:
    """Run incremental re-indexing pipeline."""

    print(f"Incremental Re-indexing Pipeline")
    print(f"Model: {model}")
    print(f"Batch size: {batch_size}")
    if limit:
        print(f"Limit: {limit} files")
    print("-" * 60)

    # Connect to database
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

    stats = {
        "model": model,
        "started_at": datetime.now().isoformat(),
        "files_processed": 0,
        "files_success": 0,
        "files_failed": 0,
        "batches_completed": 0,
        "total_time_ms": 0,
        "dry_run": dry_run,
    }

    try:
        # Get initial status
        status = await get_reindex_status(conn, model)
        print(f"Initial status:")
        print(f"  Total files: {status.total_files:,}")
        print(f"  Indexed with {model}: {status.indexed_with_model:,}")
        print(f"  Missing: {status.missing_embeddings:,}")
        print(f"  Complete: {status.percent_complete:.1f}%")
        print()

        if dry_run:
            print("DRY RUN - No changes will be made")
            return stats

        # Get files to reindex
        files = await get_files_to_reindex(conn, model, limit)

        if not files:
            print("No files need re-indexing!")
            return stats

        print(f"Re-indexing {len(files)} files...")
        print()

        # Process in batches
        total_batches = (len(files) + batch_size - 1) // batch_size
        start_time = time.perf_counter()

        async with httpx.AsyncClient() as client:
            for i in range(0, len(files), batch_size):
                batch_num = i // batch_size + 1
                batch = files[i : i + batch_size]

                print(
                    f"Batch {batch_num}/{total_batches}: Processing {len(batch)} files..."
                )

                success, failed, batch_time = await reindex_batch(
                    conn, client, model, batch
                )

                stats["files_processed"] += len(batch)
                stats["files_success"] += success
                stats["files_failed"] += failed
                stats["batches_completed"] += 1

                # Progress update
                elapsed = time.perf_counter() - start_time
                files_remaining = len(files) - stats["files_processed"]
                rate = stats["files_processed"] / elapsed if elapsed > 0 else 0
                eta = files_remaining / rate if rate > 0 else 0

                print(
                    f"  Success: {success}, Failed: {failed}, Time: {batch_time:.0f}ms"
                )
                print(f"  Progress: {stats['files_processed']}/{len(files)} files")
                print(f"  Rate: {rate:.1f} files/sec, ETA: {eta / 60:.1f} min")
                print()

                # Small delay between batches to not overwhelm API
                await asyncio.sleep(0.1)

        # Final stats
        total_time = (time.perf_counter() - start_time) * 1000
        stats["total_time_ms"] = total_time
        stats["completed_at"] = datetime.now().isoformat()

        # Get final status
        final_status = await get_reindex_status(conn, model)

        print("-" * 60)
        print("Re-indexing Complete!")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Success: {stats['files_success']}")
        print(f"  Failed: {stats['files_failed']}")
        print(f"  Batches: {stats['batches_completed']}")
        print(f"  Total time: {total_time / 1000:.1f} sec")
        print(f"  Avg time/file: {total_time / stats['files_processed']:.0f}ms")
        print()
        print(f"Final status for {model}:")
        print(
            f"  Indexed: {final_status.indexed_with_model:,}/{final_status.total_files:,}"
        )
        print(f"  Complete: {final_status.percent_complete:.1f}%")

    finally:
        await conn.close()

    return stats


async def print_status(model: Optional[str] = None):
    """Print re-indexing status for all or specific model."""

    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

    try:
        if model:
            status = await get_reindex_status(conn, model)
            print(f"Status for model: {model}")
            print(f"  Total files: {status.total_files:,}")
            print(f"  Indexed: {status.indexed_with_model:,}")
            print(f"  Missing: {status.missing_embeddings:,}")
            print(f"  Complete: {status.percent_complete:.1f}%")
            print(f"  Last updated: {status.last_updated}")
        else:
            # Show all models
            rows = await conn.fetch(
                """
                SELECT model, COUNT(*) as count
                FROM file_embeddings
                GROUP BY model
                ORDER BY count DESC
                """
            )

            total = await conn.fetchval("SELECT COUNT(*) FROM files")

            print(f"Re-indexing Status (Total files: {total:,})")
            print("-" * 60)
            print(f"{'Model':<40} {'Indexed':<12} {'% Complete':<12}")
            print("-" * 60)

            for row in rows:
                pct = (row["count"] / total * 100) if total > 0 else 0
                print(f"{row['model']:<40} {row['count']:<12,} {pct:<12.1f}%")

            # Show missing
            if rows:
                total_indexed = sum(r["count"] for r in rows)
                missing = total - total_indexed
                if missing > 0:
                    print(
                        f"{'<unindexed>':<40} {missing:<12,} {(missing / total * 100):.1f}%"
                    )

    finally:
        await conn.close()


async def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Incremental re-indexing pipeline for embedding model upgrades"
    )
    parser.add_argument(
        "--model",
        default="text-embedding-004",
        help="Embedding model to use (default: text-embedding-004)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for embedding generation (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of files to process (default: all)"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show re-indexing status and exit"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    if args.status:
        await print_status(args.model)
        return

    # Run re-indexing
    stats = await run_reindex(
        model=args.model,
        batch_size=args.batch_size,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    # Save stats to file
    if not args.dry_run and stats["files_processed"] > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"reindex_stats_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(stats, f, indent=2)

        print(f"\nStats saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
