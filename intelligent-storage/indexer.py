#!/usr/bin/env python3
"""Intelligent Storage System - File Indexing Pipeline (Async Edition)"""

import asyncio
import os
import sys
import json
import hashlib
import mimetypes
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
import asyncpg
import httpx

# ── Config ──────────────────────────────────────────────────
from config import (
    EMBED_MODEL,
    EMBED_DIM,
    BATCH_SIZE,
    DB_POOL_MAX,
    DB_POOL_MIN,
    INDEXER_DYNAMIC_BATCH,
    INDEXER_ENABLE_PRESCAN,
    INDEXER_MAX_BATCH,
    INDEXER_MAX_CHUNK_FILE_MB,
    INDEXER_MIN_BATCH,
    LOW_MEMORY_MODE,
    TEXT_PREVIEW_LEN,
    MAX_EMBED_TEXT,
    SCAN_PATHS,
    SKIP_DIRS,
)
from db import init_pool, close_pool, get_conn

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".rs",
    ".go",
    ".rb",
    ".php",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".md",
    ".txt",
    ".rst",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".r",
    ".lua",
    ".env",
    ".gitignore",
    ".dockerfile",
    "Dockerfile",
    "Makefile",
    ".mk",
    ".log",
    ".tex",
    ".bib",
    ".org",
}

# Extension → category mapping
CATEGORY_MAP = {
    "code": {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".rs",
        ".go",
        ".rb",
        ".php",
        ".sh",
        ".bash",
        ".lua",
        ".r",
        ".sql",
    },
    "document": {
        ".md",
        ".txt",
        ".rst",
        ".pdf",
        ".doc",
        ".docx",
        ".odt",
        ".tex",
        ".org",
    },
    "data": {
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".xml",
        ".parquet",
        ".sqlite",
        ".db",
    },
    "config": {".ini", ".cfg", ".conf", ".env", ".gitignore", ".editorconfig", ".toml"},
    "image": {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".bmp",
        ".ico",
        ".tiff",
    },
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"},
    "archive": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"},
    "binary": {".exe", ".dll", ".so", ".dylib", ".bin", ".AppImage"},
}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("indexer")

MAX_CHUNK_FILE_BYTES = INDEXER_MAX_CHUNK_FILE_MB * 1024 * 1024
_RUNTIME_BATCH_SIZE = BATCH_SIZE


def _detect_runtime_batch_size() -> int:
    """Compute a safe embedding batch size for current host resources."""
    batch_size = BATCH_SIZE
    if not INDEXER_DYNAMIC_BATCH:
        return max(INDEXER_MIN_BATCH, min(batch_size, INDEXER_MAX_BATCH))

    try:
        import psutil

        available_bytes = psutil.virtual_memory().available
        if LOW_MEMORY_MODE or available_bytes < 2 * 1024**3:
            batch_size = min(batch_size, 6)
        elif available_bytes < 4 * 1024**3:
            batch_size = min(batch_size, 12)
        elif available_bytes < 8 * 1024**3:
            batch_size = min(batch_size, 24)
    except Exception:
        # Keep configured batch if host memory telemetry is unavailable.
        pass

    return max(INDEXER_MIN_BATCH, min(batch_size, INDEXER_MAX_BATCH))


# Global operation ID for progress reporting
_operation_id = None
_CONTROL_API_KEY = os.environ.get("ISN_CONTROL_API_KEY", "").strip()

async def report_progress_to_server(stats: dict, current_item: str = "", status_message: str = "", success: bool = None, total_items: int = None):
    """Report progress back to the API server."""
    if not _operation_id:
        return
    
    try:
        report = {
            "items_processed": stats["indexed"],
            "current_item": os.path.basename(current_item) if current_item else "",
            "status_message": status_message
        }
        if success is not None:
            report["success"] = success
        if total_items is not None:
            report["total_items"] = total_items
            
        client = await get_http_client()
        # We assume the API server is on localhost:8000
        headers = {"X-ISN-Control-Key": _CONTROL_API_KEY} if _CONTROL_API_KEY else {}
        await client.post(
            f"http://localhost:8000/api/control/progress/{_operation_id}",
            json=report,
            headers=headers,
        )
    except Exception as e:
        log.warning(f"Failed to report progress: {e}")

# Global HTTP client for async requests
_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create async HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=120.0)
    return _http_client


async def close_http_client():
    """Close the HTTP client."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


def sha256_file(path: str, chunk_size: int = 65536) -> str | None:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return None


def read_preview(path: str, ext: str) -> str | None:
    """Read text preview from file."""
    if ext.lower() not in TEXT_EXTENSIONS:
        return None
    try:
        with open(path, "r", errors="replace") as f:
            return f.read(TEXT_PREVIEW_LEN).replace(chr(0), "")
    except (PermissionError, OSError):
        return None


def chunk_file(path: str, ext: str, size_bytes: int) -> list[str]:
    """
    Phase 3D: Content-aware chunking of files.

    Returns a list of content chunks based on file type:
    - Python: split on \ndef and \nclass boundaries
    - Markdown: split on \n# and \n## headings
    - JS/TS: split on \nfunction and \nconst at top level
    - Others: split on double-newline (paragraph boundaries)
    """
    if ext.lower() not in TEXT_EXTENSIONS:
        return []

    if size_bytes > MAX_CHUNK_FILE_BYTES:
        # Skip deep chunking for very large files to keep memory stable.
        return []

    try:
        with open(path, "r", errors="replace") as f:
            content = f.read()
    except (PermissionError, OSError):
        return []

    if not content:
        return []

    ext_lower = ext.lower()
    chunks = []

    # Python: split on function and class definitions
    if ext_lower == ".py":
        import re

        # Split on 'def ' or 'class ' at start of line
        pattern = r"\n(?=(?:def |class ))"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                chunks.append(part[:MAX_EMBED_TEXT])

    # Markdown: split on headings
    elif ext_lower == ".md":
        import re

        # Split on # or ## at start of line
        pattern = r"\n(?=(?:#{1,2} ))"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                chunks.append(part[:MAX_EMBED_TEXT])

    # JavaScript/TypeScript: split on function declarations
    elif ext_lower in (".js", ".ts", ".jsx", ".tsx"):
        import re

        # Split on function declarations or const/let/var assignments
        pattern = r"\n(?=(?:function |const |let |var |export (?:default )?(?:function |class )))"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                chunks.append(part[:MAX_EMBED_TEXT])

    # Java/C/C++: split on method boundaries
    elif ext_lower in (".java", ".c", ".cpp", ".h", ".hpp"):
        import re

        # Split on method/function definitions
        pattern = r"\n(?=(?:(?:public |private |protected |static |final )*(?:\w+\s+)?\w+\s*\(|\w+\s+\w+\s*\()))"
        parts = re.split(pattern, content)
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                chunks.append(part[:MAX_EMBED_TEXT])

    # Default: split on double-newline (paragraphs)
    else:
        parts = content.split("\n\n")
        for part in parts:
            part = part.strip()
            if part:
                chunks.append(part[:MAX_EMBED_TEXT])

    return chunks if chunks else [content[:MAX_EMBED_TEXT]]


def categorize(ext: str, mime_type: str | None) -> str:
    """Categorize file by extension and mime type."""
    ext = ext.lower() if ext else ""
    for cat, exts in CATEGORY_MAP.items():
        if ext in exts:
            return cat
    if mime_type:
        mt = mime_type.split("/")[0]
        if mt in ("image", "audio", "video", "text"):
            return mt
    return "other"


def detect_tags(name: str, ext: str, path: str, preview: str | None) -> set[str]:
    """Rule-based tag detection from filename, extension, path, content."""
    tags = set()
    ext = ext.lower() if ext else ""

    # Language tags
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".rs": "rust",
        ".go": "golang",
        ".rb": "ruby",
        ".cpp": "cpp",
        ".c": "c",
        ".php": "php",
        ".sh": "shell",
        ".r": "r-lang",
        ".lua": "lua",
        ".sql": "sql",
    }
    if ext in lang_map:
        tags.add(lang_map[ext])

    # Framework detection from content
    if preview:
        p = preview.lower()
        fw_patterns = {
            "fastapi": "fastapi",
            "flask": "flask",
            "django": "django",
            "react": "react",
            "next": "nextjs",
            "express": "express",
            "pytorch": "pytorch",
            "tensorflow": "tensorflow",
            "langchain": "langchain",
            "openai": "openai",
        }
        for pattern, tag in fw_patterns.items():
            if pattern in p:
                tags.add(tag)

    # Path-based tags
    path_lower = path.lower()
    if "test" in path_lower:
        tags.add("test")
    if "config" in path_lower or "conf" in path_lower:
        tags.add("config")
    if "doc" in path_lower:
        tags.add("documentation")
    if "backup" in path_lower:
        tags.add("backup")

    return tags


def extract_code_features(ext: str, preview: str | None) -> str:
    """Extract lightweight symbols to improve code retrieval relevance."""
    if not preview:
        return ""

    ext = ext.lower()
    symbols: list[str] = []

    try:
        import re

        if ext == ".py":
            symbols.extend(re.findall(r"^\s*(?:def|class)\s+([A-Za-z_]\w*)", preview, re.MULTILINE))
            symbols.extend(re.findall(r"^\s*import\s+([A-Za-z_]\w*)", preview, re.MULTILINE))
        elif ext in {".js", ".ts", ".jsx", ".tsx"}:
            symbols.extend(re.findall(r"^\s*(?:function|class)\s+([A-Za-z_]\w*)", preview, re.MULTILINE))
            symbols.extend(
                re.findall(
                    r"^\s*(?:const|let|var)\s+([A-Za-z_]\w*)\s*=",
                    preview,
                    re.MULTILINE,
                )
            )
            symbols.extend(re.findall(r"from\s+['\"]([^'\"]+)['\"]", preview))
        elif ext in {".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".go"}:
            symbols.extend(re.findall(r"^\s*(?:class|struct|interface)\s+([A-Za-z_]\w*)", preview, re.MULTILINE))
            symbols.extend(re.findall(r"^\s*(?:fn|func)\s+([A-Za-z_]\w*)", preview, re.MULTILINE))
    except Exception:
        return ""

    # Keep it short to avoid noisy embeddings.
    deduped = []
    seen = set()
    for sym in symbols:
        token = sym.strip()
        if token and token not in seen:
            seen.add(token)
            deduped.append(token)
        if len(deduped) >= 20:
            break

    return " ".join(deduped)


async def get_embeddings(texts: list[str]) -> list[list[float] | None]:
    """Get embeddings from Gemini in batch (async version)."""
    import gemini_client

    if not texts:
        return []

    if len(texts) > _RUNTIME_BATCH_SIZE:
        batches: list[list[float] | None] = []
        for i in range(0, len(texts), _RUNTIME_BATCH_SIZE):
            batches.extend(await get_embeddings(texts[i : i + _RUNTIME_BATCH_SIZE]))
        return batches

    return await gemini_client.get_embeddings(texts)


async def ensure_directory(
    conn: asyncpg.Connection, path: str, partition: str, dir_cache: dict
) -> int:
    """Insert directory and parents, return directory id (async version)."""
    if path in dir_cache:
        return dir_cache[path]

    parent_path = str(Path(path).parent)
    parent_id = None
    if parent_path != path:
        parent_id = await ensure_directory(conn, parent_path, partition, dir_cache)

    depth = path.count("/") - 1
    row = await conn.fetchrow(
        """
        INSERT INTO directories (path, parent_id, partition, depth)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (path) DO UPDATE SET parent_id = EXCLUDED.parent_id
        RETURNING id
    """,
        path,
        parent_id,
        partition,
        depth,
    )
    dir_id = row["id"]
    dir_cache[path] = dir_id
    return dir_id


async def ensure_tags(
    conn: asyncpg.Connection, tag_names: set[str], tag_cache: dict
) -> dict[str, int]:
    """Insert tags if needed, return {name: id} mapping (async version)."""
    new_tags = [t for t in tag_names if t not in tag_cache]
    if new_tags:
        # Use executemany for batch insert
        await conn.executemany(
            "INSERT INTO tags (name) VALUES ($1) ON CONFLICT (name) DO NOTHING",
            [(t,) for t in new_tags],
        )
        # Fetch all tag IDs
        rows = await conn.fetch(
            "SELECT id, name FROM tags WHERE name = ANY($1)", list(tag_names)
        )
        for row in rows:
            tag_cache[row["name"]] = row["id"]
    return {t: tag_cache[t] for t in tag_names if t in tag_cache}


async def ensure_embedding_model_schema(conn: asyncpg.Connection) -> None:
    """Ensure file_embeddings.model exists and is populated."""
    try:
        await conn.execute(
            """
            ALTER TABLE file_embeddings
            ADD COLUMN IF NOT EXISTS model TEXT DEFAULT 'text-embedding-004'
            """
        )
        await conn.execute(
            """
            UPDATE file_embeddings
            SET model = 'text-embedding-004'
            WHERE model IS NULL OR model = ''
            """
        )
    except Exception as e:
        log.warning(f"Embedding model schema check failed: {e}")


async def scan_and_index(conn: asyncpg.Connection, force: bool = False):
    """Main indexing pipeline (async version)."""
    dir_cache = {}
    tag_cache = {}
    stats = {"scanned": 0, "indexed": 0, "skipped": 0, "errors": 0, "embedded": 0}
    await ensure_embedding_model_schema(conn)

    # Preload existing tag cache
    rows = await conn.fetch("SELECT id, name FROM tags")
    for row in rows:
        tag_cache[row["name"]] = row["id"]

    # Preload existing file mtimes for skip logic
    rows = await conn.fetch("SELECT path, file_modified_at, size_bytes FROM files")
    existing = {r["path"]: (r["file_modified_at"], r["size_bytes"]) for r in rows}
    chunking_available = await conn.fetchval(
        "SELECT to_regclass('public.file_chunks') IS NOT NULL"
    )
    if not chunking_available:
        log.warning(
            "file_chunks table not found; chunk-level indexing disabled. "
            "Run migrations/003_content_chunking.sql to enable."
        )

    embed_queue = []  # (file_id, text_for_embedding)

    # Optional pre-scan (disabled by default to avoid double I/O on first index).
    total_files = None
    if INDEXER_ENABLE_PRESCAN:
        total_files = 0
        for scan_root in SCAN_PATHS:
            if os.path.ismount(scan_root) or os.path.isdir(scan_root):
                for _, _, filenames in os.walk(scan_root):
                    total_files += len(filenames)
        log.info(f"Total files to scan: {total_files}")
        await report_progress_to_server(
            stats,
            status_message="Starting scan...",
            total_items=total_files,
        )
    else:
        await report_progress_to_server(stats, status_message="Starting scan...")

    for scan_root, partition in SCAN_PATHS.items():
        if not os.path.ismount(scan_root) and not os.path.isdir(scan_root):
            log.warning(f"Skipping {scan_root} - not mounted")
            continue

        log.info(f"Scanning {scan_root} ({partition})...")

        for dirpath, dirnames, filenames in os.walk(scan_root):
            # Skip unwanted directories
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            dir_id = await ensure_directory(conn, dirpath, partition, dir_cache)

            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                stats["scanned"] += 1

                try:
                    st = os.stat(fpath)
                except (PermissionError, OSError):
                    stats["errors"] += 1
                    continue

                mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                size = st.st_size

                # Skip if unchanged
                if not force and fpath in existing:
                    ex_mtime, ex_size = existing[fpath]
                    if ex_mtime and ex_size == size:
                        delta_seconds = abs((ex_mtime - mtime).total_seconds())
                    else:
                        delta_seconds = None
                    if delta_seconds is not None and delta_seconds < 1:
                        stats["skipped"] += 1
                        continue

                ext = Path(fname).suffix
                mime = mimetypes.guess_type(fname)[0] or ""
                preview = read_preview(fpath, ext)
                category = categorize(ext, mime)

                # Only hash files < 100MB to avoid slowdowns
                file_hash = sha256_file(fpath) if size < 100_000_000 else None

                metadata = {
                    "category": category,
                    "tags": [],
                }

                # Detect tags
                detected_tags = detect_tags(fname, ext, fpath, preview)
                metadata["tags"] = list(detected_tags)

                try:
                    async with conn.transaction():
                        row = await conn.fetchrow(
                            """
                            INSERT INTO files (path, name, extension, directory_id, size_bytes,
                                mime_type, sha256, partition, file_modified_at, metadata, content_preview)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (path) DO UPDATE SET
                                name=EXCLUDED.name, extension=EXCLUDED.extension,
                                directory_id=EXCLUDED.directory_id, size_bytes=EXCLUDED.size_bytes,
                                mime_type=EXCLUDED.mime_type, sha256=EXCLUDED.sha256,
                                file_modified_at=EXCLUDED.file_modified_at,
                                metadata=EXCLUDED.metadata, content_preview=EXCLUDED.content_preview
                            RETURNING id
                        """,
                            fpath,
                            fname,
                            ext,
                            dir_id,
                            size,
                            mime,
                            file_hash,
                            partition,
                            mtime,
                            json.dumps(metadata),
                            preview,
                        )
                        file_id = row["id"]
                        stats["indexed"] += 1

                        # Insert tags
                        if detected_tags:
                            tag_ids = await ensure_tags(conn, detected_tags, tag_cache)
                            for tname, tid in tag_ids.items():
                                await conn.execute(
                                    """
                                    INSERT INTO file_tags (file_id, tag_id) VALUES ($1, $2)
                                    ON CONFLICT DO NOTHING
                                """,
                                    file_id,
                                    tid,
                                )

                        # Phase 3D: Process content chunks
                        chunks = chunk_file(fpath, ext, size) if chunking_available else []
                        if chunks:
                            # Store chunks and their embeddings
                            chunk_data = []
                            for idx, chunk_content in enumerate(
                                chunks[:10]
                            ):  # Max 10 chunks per file
                                chunk_data.append((file_id, idx, chunk_content))

                            # Insert chunks in bulk for better indexing throughput.
                            await conn.executemany(
                                """
                                INSERT INTO file_chunks (file_id, chunk_index, content)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (file_id, chunk_index) DO UPDATE
                                SET content = EXCLUDED.content, created_at = now()
                            """,
                                chunk_data,
                            )

                            # Skip update file chunk count for now as column is missing and permissions are restricted
                            # await conn.execute(
                            #     "UPDATE files SET chunk_count = $1 WHERE id = $2",
                            #     len(chunk_data),
                            #     file_id,
                            # )

                            # Queue chunk embeddings for processing
                            for chunk_file_id, chunk_idx, chunk_content in chunk_data:
                                embed_queue.append(
                                    (f"chunk:{chunk_file_id}:{chunk_idx}", chunk_content)
                                )

                        # Queue for file-level embedding
                        code_features = (
                            extract_code_features(ext, preview)
                            if category == "code"
                            else ""
                        )
                        embed_text = (
                            f"{fname} {ext} {category} {' '.join(detected_tags)} "
                            f"{code_features} {preview or ''}"
                        )
                        embed_queue.append((f"file:{file_id}", embed_text[:MAX_EMBED_TEXT]))

                except Exception as e:
                    log.error(f"Error indexing {fpath}: {e}")
                    dir_cache.clear()
                    stats["errors"] += 1
                    continue

                # Process embedding batch
                if len(embed_queue) >= _RUNTIME_BATCH_SIZE:
                    await _process_embeddings(conn, embed_queue, stats)
                    embed_queue = []

                # Log progress every 10 files for better real-time feedback
                if stats["indexed"] % 10 == 0 and stats["indexed"] > 0:
                    log.info(
                        f"Progress: {stats['indexed']} indexed, {stats['scanned']} scanned"
                    )
                    await report_progress_to_server(
                        stats,
                        current_item=fpath,
                        status_message="Indexing files...",
                        total_items=total_files,
                    )

    # Process remaining embeddings
    if embed_queue:
        await _process_embeddings(conn, embed_queue, stats)
        await report_progress_to_server(stats, status_message="Finalizing embeddings...")

    return stats


async def _process_embeddings(conn: asyncpg.Connection, queue: list, stats: dict):
    """Process a batch of embeddings (async version) - Phase 3D: handles files and chunks."""
    texts = [t for _, t in queue]
    embeddings = await get_embeddings(texts)

    for (entity_id, _), emb in zip(queue, embeddings):
        if emb is None:
            continue

        try:
            # Check if this is a chunk or file embedding based on ID format
            if isinstance(entity_id, str) and entity_id.startswith("chunk:"):
                # Format: chunk:file_id:chunk_index
                parts = entity_id.split(":")
                if len(parts) == 3:
                    file_id = int(parts[1])
                    chunk_idx = int(parts[2])
                    await conn.execute(
                        """
                        UPDATE file_chunks
                        SET embedding = $1::vector
                        WHERE file_id = $2 AND chunk_index = $3
                    """,
                        str(emb),
                        file_id,
                        chunk_idx,
                    )
                    stats["embedded"] += 1
            elif isinstance(entity_id, str) and entity_id.startswith("file:"):
                # Regular file embedding
                file_id = int(entity_id.split(":")[1])
                await conn.execute(
                    """
                    INSERT INTO file_embeddings (file_id, embedding, model)
                    VALUES ($1, $2::vector, $3)
                    ON CONFLICT (file_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        model = EXCLUDED.model,
                        created_at = now()
                """,
                    file_id,
                    str(emb),
                    EMBED_MODEL,
                )
                stats["embedded"] += 1
            else:
                # Legacy format - assume it's a file_id
                await conn.execute(
                    """
                    INSERT INTO file_embeddings (file_id, embedding, model)
                    VALUES ($1, $2::vector, $3)
                    ON CONFLICT (file_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        model = EXCLUDED.model,
                        created_at = now()
                """,
                    entity_id,
                    str(emb),
                    EMBED_MODEL,
                )
                stats["embedded"] += 1
        except Exception as e:
            log.error(f"Embedding insert error for entity {entity_id}: {e}")


async def build_knowledge_graph(conn: asyncpg.Connection):
    """Build AGE knowledge graph from indexed files (async version)."""
    # Load AGE if available.
    try:
        await conn.execute("LOAD 'age';")
        await conn.execute("SET search_path = ag_catalog, public;")
        graph_exists = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'storage_graph'
            )
            """
        )
        if not graph_exists:
            await conn.fetchval("SELECT ag_catalog.create_graph('storage_graph')")
    except Exception as e:
        log.warning(f"Skipping knowledge graph build (AGE unavailable): {e}")
        return

    log.info("Building knowledge graph...")

    # Create directory nodes
    rows = await conn.fetch("SELECT id, path, partition FROM directories")
    for row in rows:
        did, dpath, partition = row["id"], row["path"], row["partition"]
        label = Path(dpath).name or partition
        try:
            await conn.execute(
                """
                SELECT * FROM cypher('storage_graph', $$
                    MERGE (d:Directory {db_id: %s, path: %s, name: %s, partition: %s})
                    RETURN d
                $$) AS (v agtype)
            """
                % (did, repr(dpath), repr(label), repr(partition))
            )
        except Exception as e:
            log.warning(f"Skipping directory node {dpath}: {e}")

    # Create file nodes for key files (not every file, just notable ones)
    rows = await conn.fetch("""
        SELECT f.id, f.path, f.name, f.extension, f.metadata->>'category' as cat
        FROM files f
        WHERE f.extension IN ('.py','.js','.ts','.md','.json','.yaml','.yml','.sql','.sh','.toml','.cfg')
           OR f.size_bytes > 1000000
        LIMIT 5000
    """)
    for row in rows:
        fid, fpath, fname, ext, cat = (
            row["id"],
            row["path"],
            row["name"],
            row["extension"],
            row["cat"],
        )
        try:
            await conn.execute(
                """
                SELECT * FROM cypher('storage_graph', $$
                    MERGE (f:File {db_id: %s, path: %s, name: %s, extension: %s, category: %s})
                    RETURN f
                $$) AS (v agtype)
            """
                % (fid, repr(fpath), repr(fname), repr(ext or ""), repr(cat or "other"))
            )
        except Exception as e:
            log.warning(f"Skipping file node {fpath}: {e}")

    # Create CONTAINS edges (directory → file)
    rows = await conn.fetch("""
        SELECT f.id AS file_id, d.id AS dir_id FROM files f
        JOIN directories d ON f.directory_id = d.id
        WHERE f.extension IN ('.py','.js','.ts','.md','.json','.yaml','.yml','.sql','.sh','.toml','.cfg')
           OR f.size_bytes > 1000000
        LIMIT 5000
    """)
    for row in rows:
        fid, did = row["file_id"], row["dir_id"]
        try:
            await conn.execute(
                """
                SELECT * FROM cypher('storage_graph', $$
                    MATCH (d:Directory {db_id: %s}), (f:File {db_id: %s})
                    MERGE (d)-[:CONTAINS]->(f)
                    RETURN d, f
                $$) AS (d agtype, f agtype)
            """
                % (did, fid)
            )
        except Exception as e:
            log.warning(f"Skipping CONTAINS edge dir={did} file={fid}: {e}")

    # Create tag nodes and edges
    rows = await conn.fetch("""
        SELECT DISTINCT t.name FROM tags t
        JOIN file_tags ft ON ft.tag_id = t.id
    """)
    for row in rows:
        tname = row["name"]
        try:
            await conn.execute(
                """
                SELECT * FROM cypher('storage_graph', $$
                    MERGE (t:Tag {name: %s})
                    RETURN t
                $$) AS (v agtype)
            """
                % repr(tname)
            )
        except Exception as e:
            log.warning(f"Skipping tag node {tname}: {e}")

    log.info("Knowledge graph built")


async def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Intelligent Storage Indexer")
    parser.add_argument("--force", action="store_true", help="Force re-indexing of all files")
    parser.add_argument("--operation-id", type=str, help="Optional operation ID for progress tracking")
    args = parser.parse_args()

    start = time.time()
    log.info("=== Intelligent Storage Indexer (Async Edition) ===")
    if args.force:
        log.info("🚀 Force mode enabled: Re-indexing all files to populate chunks and embeddings")

    global _operation_id, _RUNTIME_BATCH_SIZE
    _operation_id = args.operation_id

    _RUNTIME_BATCH_SIZE = _detect_runtime_batch_size()
    pool_min = DB_POOL_MIN
    pool_max = DB_POOL_MAX
    if LOW_MEMORY_MODE:
        pool_min = min(pool_min, 1)
        pool_max = min(pool_max, 4)
    if pool_max < pool_min:
        pool_max = pool_min

    log.info(
        "Indexer runtime profile: batch=%d, prescan=%s, max_chunk_file=%dMB, pool=[%d,%d]",
        _RUNTIME_BATCH_SIZE,
        INDEXER_ENABLE_PRESCAN,
        INDEXER_MAX_CHUNK_FILE_MB,
        pool_min,
        pool_max,
    )

    await init_pool(min_size=pool_min, max_size=pool_max)
    try:
        async with get_conn() as conn:
            stats = await scan_and_index(conn, force=args.force)

        await report_progress_to_server(stats, status_message="Indexing complete", success=True)

        elapsed = time.time() - start
        log.info(f"Indexing complete in {elapsed:.1f}s")
        log.info(f"  Scanned: {stats['scanned']}")
        log.info(f"  Indexed: {stats['indexed']}")
        log.info(f"  Embedded: {stats['embedded']}")
        log.info(f"  Skipped (unchanged): {stats['skipped']}")
        log.info(f"  Errors: {stats['errors']}")

        log.info("Building knowledge graph...")
        async with get_conn() as conn:
            await build_knowledge_graph(conn)
    finally:
        await close_pool()
        await close_http_client()
        log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
