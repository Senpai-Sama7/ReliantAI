"""Centralized configuration for Intelligent Storage Nexus."""

import json
import os
from urllib.parse import quote_plus


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse environment variable as boolean."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


# Database
DB_HOST = os.environ.get("ISN_DB_HOST", "localhost")
DB_PORT = os.environ.get("ISN_DB_PORT", "5433")
DB_NAME = os.environ.get("ISN_DB_NAME", "intelligent_storage")
DB_USER = os.environ.get("ISN_DB_USER", "storage_admin")
DB_PASS = os.environ.get("ISN_DB_PASS", "storage_local_2026")
_DB_USER_ESCAPED = quote_plus(DB_USER)
_DB_PASS_ESCAPED = quote_plus(DB_PASS)
DB_DSN = os.environ.get("ISN_DB_DSN") or (
    f"postgresql://{_DB_USER_ESCAPED}:{_DB_PASS_ESCAPED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
DB_POOL_MIN = int(os.environ.get("ISN_DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.environ.get("ISN_DB_POOL_MAX", "10"))
DB_COMMAND_TIMEOUT_SEC = int(os.environ.get("ISN_DB_COMMAND_TIMEOUT_SEC", "60"))
if DB_POOL_MIN < 1:
    DB_POOL_MIN = 1
if DB_POOL_MAX < DB_POOL_MIN:
    DB_POOL_MAX = DB_POOL_MIN

# Gemini API
GEMINI_API_KEY = os.environ.get("ISN_GEMINI_API_KEY", "")
EMBED_MODEL = os.environ.get("ISN_EMBED_MODEL", "text-embedding-004")
EMBED_DIM = int(os.environ.get("ISN_EMBED_DIM", "768"))
CHAT_MODEL = os.environ.get("ISN_CHAT_MODEL", "gemini-3.1-flash")

# Indexer
BATCH_SIZE = int(os.environ.get("ISN_BATCH_SIZE", "32"))
TEXT_PREVIEW_LEN = int(os.environ.get("ISN_TEXT_PREVIEW_LEN", "500"))
MAX_EMBED_TEXT = int(os.environ.get("ISN_MAX_EMBED_TEXT", "2000"))
INDEXER_DYNAMIC_BATCH = _env_bool("ISN_INDEXER_DYNAMIC_BATCH", default=True)
INDEXER_MIN_BATCH = int(os.environ.get("ISN_INDEXER_MIN_BATCH", "4"))
INDEXER_MAX_BATCH = int(os.environ.get("ISN_INDEXER_MAX_BATCH", "64"))
INDEXER_ENABLE_PRESCAN = _env_bool("ISN_INDEXER_ENABLE_PRESCAN", default=False)
INDEXER_MAX_CHUNK_FILE_MB = int(os.environ.get("ISN_INDEXER_MAX_CHUNK_FILE_MB", "8"))
LOW_MEMORY_MODE = _env_bool("ISN_LOW_MEMORY_MODE", default=False)
if INDEXER_MIN_BATCH < 1:
    INDEXER_MIN_BATCH = 1
if INDEXER_MAX_BATCH < INDEXER_MIN_BATCH:
    INDEXER_MAX_BATCH = INDEXER_MIN_BATCH
if INDEXER_MAX_CHUNK_FILE_MB < 1:
    INDEXER_MAX_CHUNK_FILE_MB = 1

# Tree of Thoughts
TOT_MAX_DEPTH = int(os.environ.get("ISN_TOT_MAX_DEPTH", "3"))
TOT_BRANCHING_FACTOR = int(os.environ.get("ISN_TOT_BRANCHING_FACTOR", "3"))
TOT_SIMILARITY_THRESHOLD = float(
    os.environ.get("ISN_TOT_SIMILARITY_THRESHOLD", "0.75")
)

# Scan paths (overridable via ISN_SCAN_PATHS_JSON)
DEFAULT_SCAN_PATHS = {
    "/mnt/external": "DATA_HUB",
    "/mnt/DMZ": "DMZ",
}


def _load_scan_paths() -> dict[str, str]:
    raw_scan_paths = os.environ.get("ISN_SCAN_PATHS_JSON")
    if not raw_scan_paths:
        return DEFAULT_SCAN_PATHS

    try:
        parsed = json.loads(raw_scan_paths)
        if isinstance(parsed, dict):
            scan_paths = {
                str(path): str(partition)
                for path, partition in parsed.items()
                if str(path).strip() and str(partition).strip()
            }
            if scan_paths:
                return scan_paths
    except json.JSONDecodeError:
        pass

    return DEFAULT_SCAN_PATHS


SCAN_PATHS = _load_scan_paths()

SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".cache",
    "$RECYCLE.BIN",
    "System Volume Information",
    ".Trash-1000",
}

# CORS Origins (comma-separated)
CORS_ORIGINS = os.environ.get(
    "ISN_CORS_ORIGINS", "http://localhost:8000,http://localhost:8080"
).split(",")

# Rate Limiting
RATE_LIMIT_SEARCH = os.environ.get("ISN_RATE_LIMIT_SEARCH", "30/minute")
RATE_LIMIT_READ = os.environ.get("ISN_RATE_LIMIT_READ", "100/minute")

# Graph fallback tuning
GRAPH_AUTO_TUNE_THRESHOLD = _env_bool("ISN_GRAPH_AUTO_TUNE_THRESHOLD", default=True)
GRAPH_MIN_EDGE_SIM_THRESHOLD = float(
    os.environ.get("ISN_GRAPH_MIN_EDGE_SIM_THRESHOLD", "0.72")
)
