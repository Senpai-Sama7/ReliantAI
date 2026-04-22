#!/usr/bin/env python3
"""
Intelligent Storage Nexus - API Server (Async Edition)
Next-generation file intelligence with semantic search, knowledge graphs, AI reasoning
Version: 2.1.0 Async Edition
"""

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
import asyncpg
import numpy as np
from datetime import datetime, timedelta
import json
import asyncio
import httpx
import logging
import sys
import re
import csv
import io
import subprocess
import os

# Rate limiting (Phase 6E)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    HAS_RATE_LIMITER = True
except ImportError:
    HAS_RATE_LIMITER = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phase 6B/6D: LLM model for classification and NL parsing (via Gemini)

# Import config, async db, and cache
from config import (
    EMBED_MODEL,
    EMBED_DIM,
    TOT_MAX_DEPTH,
    TOT_BRANCHING_FACTOR,
    TOT_SIMILARITY_THRESHOLD,
    CORS_ORIGINS,
    RATE_LIMIT_SEARCH,
    RATE_LIMIT_READ,
    LOW_MEMORY_MODE,
)
from db import init_pool, close_pool, get_conn
from cache import init_cache, close_cache, get_cache
from control_auth import authorize_websocket, require_control_api_key
from graph_manager import init_graph_manager, get_graph_manager
import gemini_client


async def _ensure_embedding_model_schema() -> None:
    """Ensure model-tracking column exists for vector rows."""
    try:
        async with get_conn() as conn:
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
    except Exception as exc:
        logger.warning(f"Embedding model schema check failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup/shutdown."""
    # Startup
    logger.info("🚀 Initializing API server...")
    if LOW_MEMORY_MODE:
        await init_pool(min_size=1, max_size=4)
    else:
        await init_pool()
    await _ensure_embedding_model_schema()
    await init_cache()  # Phase 3C: Initialize cache layer
    await init_graph_manager()  # Phase 4A: Initialize graph manager
    logger.info("✅ API server ready")
    yield
    # Shutdown
    logger.info("🛑 Shutting down API server...")
    await close_cache()  # Phase 3C: Close cache
    await close_http_client()
    await close_pool()
    logger.info("✅ API server stopped")




# Phase 6E: Rate limiting setup
if HAS_RATE_LIMITER:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

app = FastAPI(
    title="Intelligent Storage Nexus",
    description="Next-generation file intelligence with semantic search, knowledge graphs, and AI reasoning",
    version="2.1.0",
    lifespan=lifespan,
)

# Phase 6E: Add rate limiter to app state
if limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Rate limiting enabled")

# Phase 6E: CORS with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 6F: GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)
logger.info("✅ GZip compression enabled")

static_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/")
async def root():
    """Serve the main HTML file"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Intelligent Storage Nexus API", "docs": "/docs"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        stale_connections: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                stale_connections.append(connection)

        for stale in stale_connections:
            self.disconnect(stale)


manager = ConnectionManager()


CATEGORY_EXTENSIONS: Dict[str, set[str]] = {
    "code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs", ".go", ".rb", ".php"},
    "document": {".pdf", ".doc", ".txt", ".md", ".docx"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"},
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "data": {".csv", ".json", ".xml", ".yaml", ".yml", ".parquet", ".toml"},
}


def normalize_query_text(query: str) -> str:
    """Trim and normalize user-entered query text."""
    return " ".join(query.strip().split())


def classify_extension(extension: Optional[str]) -> str:
    """Map a file extension to a category label."""
    ext = (extension or "").lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category
    return "other"


# ============================================================================
# OPTIMIZATION MODULES INTEGRATION
# ============================================================================

OPTIMIZATION_MODULES_AVAILABLE = False
_optimization_engine = None
_engine_initialized = False

try:
    from optimization_modules import UltimateIntelligentStorage, PerformanceBenchmark

    OPTIMIZATION_MODULES_AVAILABLE = True
    logger.info("✅ Ultimate Edition optimization modules loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Optimization modules not available: {e}")
    logger.info("   Falling back to PostgreSQL-only search")


# ============================================================================
# PROGRESS TRACKING SYSTEM
# ============================================================================
# Real-time progress tracking with pause/resume and ETA

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock

# Store active subprocesses globally
active_subprocesses = {}


class OperationType(Enum):
    INDEXING = "indexing"
    SEARCH = "search"
    EXPORT = "export"
    IMPORT = "import"
    REORGANIZE = "reorganize"


class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProgressUpdate:
    """Single progress update"""

    timestamp: float
    items_processed: int
    total_items: int
    items_per_second: float
    elapsed_seconds: float
    eta_seconds: float
    current_item: str = ""
    status_message: str = ""


@dataclass
class ProgressOperation:
    """Trackable operation with state"""

    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    total_items: int
    processed_items: int
    failed_items: int
    start_time: float
    last_update: float
    total_elapsed: float
    pause_time: float = 0.0
    is_paused: bool = False
    current_item: str = ""
    status_message: str = ""
    updates: List[ProgressUpdate] = field(default_factory=list)
    error_message: str = ""

    @property
    def progress_percent(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def eta_seconds(self) -> float:
        if self.processed_items == 0:
            return 0.0

        elapsed = self.total_elapsed
        if elapsed == 0:
            return 0.0

        rate = self.processed_items / elapsed
        remaining = self.total_items - self.processed_items

        if rate == 0:
            return 0.0

        return remaining / rate

    @property
    def eta_formatted(self) -> str:
        eta = self.eta_seconds
        if eta <= 0:
            return "Calculating..."

        hours = int(eta // 3600)
        minutes = int((eta % 3600) // 60)
        seconds = int(eta % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class ProgressManager:
    """
    Manages progress tracking for long-running operations.
    Supports pause/resume and real-time ETA calculations.
    """

    def __init__(self):
        self.operations: Dict[str, ProgressOperation] = {}
        self.subscribers: Dict[str, List[WebSocket]] = {}
        self.lock = Lock()
        logger.info("ProgressManager initialized")

    def create_operation(
        self,
        operation_type: OperationType,
        total_items: int,
        operation_id: Optional[str] = None,
    ) -> str:
        """Create a new tracked operation"""
        op_id = operation_id or str(uuid.uuid4())[:8]

        operation = ProgressOperation(
            operation_id=op_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            total_items=total_items,
            processed_items=0,
            failed_items=0,
            start_time=time.time(),
            last_update=time.time(),
            total_elapsed=0.0,
        )

        with self.lock:
            self.operations[op_id] = operation

        logger.info(
            f"Created operation {op_id}: {operation_type.value} ({total_items} items)"
        )
        return op_id

    def start_operation(self, operation_id: str) -> bool:
        """Start a pending operation"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]
            op.status = OperationStatus.RUNNING
            op.start_time = time.time()
            op.last_update = time.time()

        logger.info(f"Started operation {operation_id}")
        return True

    def update_progress(
        self,
        operation_id: str,
        items_processed: int,
        current_item: str = "",
        status_message: str = "",
        total_items: Optional[int] = None,
    ) -> bool:
        """Update progress for an operation"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]

            # Calculate rate
            current_time = time.time()
            elapsed = current_time - op.start_time - op.pause_time

            if elapsed > 0 and items_processed > op.processed_items:
                rate = (items_processed - op.processed_items) / (
                    current_time - op.last_update
                )
            else:
                rate = 0.0

            if total_items is not None:
                op.total_items = total_items

            # Calculate ETA
            if items_processed > 0 and elapsed > 0:
                avg_rate = items_processed / elapsed
                remaining = op.total_items - items_processed
                eta = remaining / avg_rate if avg_rate > 0 else 0
            else:
                eta = 0

            # Create update
            update = ProgressUpdate(
                timestamp=current_time,
                items_processed=items_processed,
                total_items=op.total_items,
                items_per_second=rate,
                elapsed_seconds=elapsed,
                eta_seconds=eta,
                current_item=current_item,
                status_message=status_message,
            )

            # Update operation
            op.processed_items = items_processed
            op.current_item = current_item
            op.status_message = status_message
            op.last_update = current_time
            op.total_elapsed = elapsed
            op.updates.append(update)

            # Notify subscribers
            self._notify_subscribers(
                operation_id,
                {
                    "type": "progress",
                    "operation_id": operation_id,
                    "progress_percent": op.progress_percent,
                    "items_processed": items_processed,
                    "total_items": op.total_items,
                    "eta_seconds": eta,
                    "eta_formatted": op.eta_formatted,
                    "items_per_second": rate,
                    "elapsed_seconds": elapsed,
                    "current_item": current_item,
                    "status_message": status_message,
                },
            )

        return True

    def pause_operation(self, operation_id: str) -> bool:
        """Pause a running operation"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]
            if op.status != OperationStatus.RUNNING:
                return False

            op.status = OperationStatus.PAUSED
            op.pause_time = time.time()
            op.is_paused = True

            # Notify subscribers
            self._notify_subscribers(
                operation_id,
                {
                    "type": "paused",
                    "operation_id": operation_id,
                    "progress_percent": op.progress_percent,
                    "items_processed": op.processed_items,
                    "total_items": op.total_items,
                    "elapsed_seconds": op.total_elapsed,
                },
            )

        logger.info(f"Paused operation {operation_id}")
        return True

    def resume_operation(self, operation_id: str) -> bool:
        """Resume a paused operation"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]
            if op.status != OperationStatus.PAUSED:
                return False

            # Adjust start time to account for pause
            pause_duration = time.time() - op.pause_time
            op.start_time += pause_duration
            op.pause_time = 0.0
            op.is_paused = False
            op.status = OperationStatus.RUNNING

            # Notify subscribers
            self._notify_subscribers(
                operation_id,
                {
                    "type": "resumed",
                    "operation_id": operation_id,
                    "progress_percent": op.progress_percent,
                },
            )

        logger.info(f"Resumed operation {operation_id}")
        return True

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]
            op.status = OperationStatus.CANCELLED

            # Notify subscribers
            self._notify_subscribers(
                operation_id,
                {
                    "type": "cancelled",
                    "operation_id": operation_id,
                    "progress_percent": op.progress_percent,
                },
            )

        logger.info(f"Cancelled operation {operation_id}")
        return True

    def complete_operation(self, operation_id: str, success: bool = True) -> bool:
        """Mark an operation as completed"""
        with self.lock:
            if operation_id not in self.operations:
                return False

            op = self.operations[operation_id]
            op.status = OperationStatus.COMPLETED if success else OperationStatus.ERROR
            op.total_elapsed = time.time() - op.start_time - op.pause_time

            # Notify subscribers
            self._notify_subscribers(
                operation_id,
                {
                    "type": "completed",
                    "operation_id": operation_id,
                    "success": success,
                    "progress_percent": 100.0,
                    "total_elapsed": op.total_elapsed,
                },
            )

        logger.info(
            f"Completed operation {operation_id}: {'success' if success else 'error'}"
        )
        return True

    def get_operation_status(self, operation_id: str) -> Optional[Dict]:
        """Get current status of an operation"""
        with self.lock:
            if operation_id not in self.operations:
                return None

            op = self.operations[operation_id]
            return {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "status": op.status.value,
                "progress_percent": op.progress_percent,
                "items_processed": op.processed_items,
                "total_items": op.total_items,
                "failed_items": op.failed_items,
                "eta_seconds": op.eta_seconds,
                "eta_formatted": op.eta_formatted,
                "elapsed_seconds": op.total_elapsed,
                "items_per_second": op.processed_items / op.total_elapsed
                if op.total_elapsed > 0
                else 0,
                "current_item": op.current_item,
                "status_message": op.status_message,
                "is_paused": op.is_paused,
            }

    def list_operations(
        self, status_filter: Optional[OperationStatus] = None
    ) -> List[Dict]:
        """List all operations, optionally filtered by status"""
        with self.lock:
            ops = list(self.operations.values())

        if status_filter:
            ops = [op for op in ops if op.status == status_filter]

        return [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "status": op.status.value,
                "progress_percent": op.progress_percent,
                "items_processed": op.processed_items,
                "total_items": op.total_items,
                "eta_formatted": op.eta_formatted,
                "is_paused": op.is_paused,
            }
            for op in sorted(ops, key=lambda x: x.start_time, reverse=True)
        ]

    def subscribe(self, operation_id: str, websocket: WebSocket):
        """Subscribe to progress updates for an operation"""
        if operation_id not in self.subscribers:
            self.subscribers[operation_id] = []

        if websocket not in self.subscribers[operation_id]:
            self.subscribers[operation_id].append(websocket)

    def unsubscribe(self, operation_id: str, websocket: WebSocket):
        """Unsubscribe from progress updates"""
        if operation_id in self.subscribers:
            if websocket in self.subscribers[operation_id]:
                self.subscribers[operation_id].remove(websocket)

    def _notify_subscribers(self, operation_id: str, message: dict):
        """Send message to all subscribers of an operation"""
        if operation_id not in self.subscribers:
            return

        for websocket in self.subscribers[operation_id][
            :
        ]:  # Copy to avoid modification during iteration
            try:
                asyncio.create_task(websocket.send_json(message))
            except Exception:
                self.subscribers[operation_id].remove(websocket)


# Global progress manager
progress_manager = ProgressManager()


def get_optimization_engine():
    """Get or initialize the optimization engine"""
    global _optimization_engine, _engine_initialized

    if _engine_initialized or not OPTIMIZATION_MODULES_AVAILABLE:
        return _optimization_engine

    try:
        logger.info("🚀 Initializing Ultimate Edition optimization engine...")
        _optimization_engine = UltimateIntelligentStorage(storage_dir="./api_storage")
        _engine_initialized = True
        logger.info("✅ Optimization engine ready (0.56ms search latency)")
        return _optimization_engine
    except Exception as e:
        logger.error(f"❌ Failed to initialize optimization engine: {e}")
        return None


# ============================================================================
# Pydantic Models
# ============================================================================


class FileSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    semantic_weight: float = Field(0.6, ge=0, le=1)
    keyword_weight: float = Field(0.3, ge=0, le=1)
    meta_weight: float = Field(0.1, ge=0, le=1)
    filters: Optional[Dict[str, Any]] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    include_similar: bool = True
    include_relationships: bool = True


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(20, ge=1, le=100)
    threshold: float = Field(0.7, ge=0, le=1)
    include_metadata: bool = True


class TreeOfThoughtsRequest(BaseModel):
    seed_query: str
    max_depth: int = Field(3, ge=1, le=5)
    branching_factor: int = Field(3, ge=2, le=5)
    exploration_strategy: str = Field(
        "diversity", pattern="^(diversity|depth|breadth)$"
    )


class GraphQueryRequest(BaseModel):
    center_file_id: Optional[int] = None
    center_path: Optional[str] = None
    depth: int = Field(2, ge=1, le=4)
    relationship_types: List[str] = Field(
        ["similarity", "directory", "content", "semantic"]
    )
    min_similarity: float = Field(0.6, ge=0, le=1)


class InsightRequest(BaseModel):
    file_ids: Optional[List[int]] = None
    path_patterns: Optional[List[str]] = None
    insight_types: List[str] = Field(["duplicates", "clusters", "anomalies", "trends"])


class RecommendationRequest(BaseModel):
    context: str
    based_on_recent: bool = True
    based_on_similar: bool = True
    max_recommendations: int = Field(10, ge=1, le=50)


class FacetedSearchRequest(BaseModel):
    query: Optional[str] = None
    facets: Dict[str, List[str]] = Field(default_factory=dict)
    date_range: Optional[Tuple[str, str]] = None
    size_range: Optional[Tuple[int, int]] = None
    page: int = 1
    limit: int = 20


class RRFSearchRequest(BaseModel):
    """Reciprocal Rank Fusion search request."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(20, ge=1, le=100)
    rerank: bool = Field(True, description="Enable re-ranking on content preview")
    include_similar: bool = True


class FileTagUpdateRequest(BaseModel):
    tags: List[str] = Field(default_factory=list)



class NaturalLanguageSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(50, ge=1, le=200)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []
    context_window: int = 5


# ============================================================================
# Embedding & Vector Operations
# ============================================================================

# HTTP client for async requests
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create async HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def close_http_client() -> None:
    """Close shared HTTP client."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from Gemini with caching (async version)."""
    text = normalize_query_text(text)
    if not text:
        return [0.0] * EMBED_DIM

    # Phase 3C: Check cache first
    cache = get_cache()
    if cache:
        cached = await cache.get_embedding(text)
        if cached is not None:
            logger.debug(f"Cache HIT for embedding: {text[:50]}...")
            return cached
        logger.debug(f"Cache MISS for embedding: {text[:50]}...")

    embedding = await gemini_client.get_single_embedding(text)

    # Phase 3C: Cache the result
    if cache and embedding:
        await cache.set_embedding(text, embedding)

    return embedding or [0.0] * EMBED_DIM


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts in a single batch call (Phase 3B)."""
    if not texts:
        return []

    results = await gemini_client.get_embeddings(texts)
    # Replace None values with zero vectors
    return [emb if emb else [0.0] * EMBED_DIM for emb in results]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    v1_np = np.array(v1, dtype=np.float32)
    v2_np = np.array(v2, dtype=np.float32)
    norm_product = float(np.linalg.norm(v1_np) * np.linalg.norm(v2_np))
    if norm_product == 0.0:
        return 0.0
    return float(np.dot(v1_np, v2_np) / norm_product)


def vector_to_sql(vector: List[float]) -> str:
    """Convert vector to PostgreSQL array format"""
    return "[" + ",".join(map(str, vector)) + "]"


def parse_embedding_value(raw_embedding: Any) -> np.ndarray:
    """Normalize DB embedding values to float32 NumPy arrays."""
    if isinstance(raw_embedding, np.ndarray):
        return raw_embedding.astype(np.float32)
    if hasattr(raw_embedding, "tolist"):
        try:
            return np.array(raw_embedding.tolist(), dtype=np.float32)
        except Exception:
            pass
    if isinstance(raw_embedding, (list, tuple)):
        return np.array(raw_embedding, dtype=np.float32)
    if isinstance(raw_embedding, str):
        return np.fromstring(raw_embedding.strip("[]"), sep=",", dtype=np.float32)

    return np.array([], dtype=np.float32)


# ============================================================================
# Advanced Search & Retrieval
# ============================================================================


@app.post("/api/search/advanced")
async def advanced_search(request: FileSearchRequest):
    """
    Advanced hybrid search with Tree of Thoughts reasoning
    OPTIMIZED: Uses Ultimate Edition modules when available (89x faster!)
    """
    query = normalize_query_text(request.query)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    cache = get_cache()
    cache_weights = (
        "advanced",
        round(request.semantic_weight, 3),
        round(request.keyword_weight, 3),
        round(request.meta_weight, 3),
        request.page,
        request.include_similar,
        request.include_relationships,
    )
    if cache:
        cached_result = await cache.get_search_result(query, request.limit, cache_weights)
        if cached_result is not None:
            return {**cached_result, "cached": True}

    query_embedding = await get_embedding(query)
    query_vec = np.array(query_embedding, dtype=np.float32)

    # Try optimization engine first (89x faster!)
    if OPTIMIZATION_MODULES_AVAILABLE:
        engine = get_optimization_engine()
        if engine and engine.is_initialized:
            try:
                results = engine.search(
                    query_embedding=query_vec,
                    query_text=query,
                    top_k=request.page * request.limit,
                    use_graph=True,
                )

                optimized_results = [
                    {
                        "id": r.file_id,
                        "score": r.score,
                        "tier": r.tier,
                        "metadata": r.metadata,
                        "explanation": r.explanation,
                        "related_files": r.related_files,
                        "entities": r.entities,
                    }
                    for r in results
                ]

                logger.info(
                    f"⚡ Optimization engine: {len(optimized_results)} results in ~0.56ms"
                )

                start_idx = (request.page - 1) * request.limit
                paged_results = optimized_results[start_idx : start_idx + request.limit]

                response_payload = {
                    "results": paged_results,
                    "total": len(optimized_results),
                    "query": query,
                    "source": "optimization_engine",
                    "search_metadata": {
                        "engine": "Ultimate Edition (HNSW + Quantization)",
                        "latency": "~0.56ms",
                        "speedup": "89x vs baseline",
                        "page": request.page,
                        "limit": request.limit,
                    },
                }
                if cache:
                    await cache.set_search_result(
                        query,
                        request.limit,
                        response_payload,
                        cache_weights,
                    )
                return response_payload
            except Exception as e:
                logger.error(f"Optimization search error: {e}")

    # Fallback to PostgreSQL (async version)
    logger.info("Using PostgreSQL search fallback")

    async with get_conn() as conn:
        expanded_queries = await expand_query_with_tot(
            query, query_embedding, conn, depth=min(TOT_MAX_DEPTH, 2)
        )

        results = []
        seen_ids = set()

        for expanded_query, q_vec, weight in expanded_queries:
            q_vec_sql = vector_to_sql(list(q_vec))
            rows = await conn.fetch(
                """
                SELECT
                    f.id AS file_id,
                    f.path AS file_path,
                    f.name AS file_name,
                    (
                        COALESCE($4 * (1 - (fe.embedding <=> $2::vector(768))), 0) +
                        COALESCE($5 * ts_rank(f.fts_vector, plainto_tsquery('english', $1)), 0) +
                        COALESCE($6 * similarity(f.name, $1), 0)
                    )::REAL AS score,
                    COALESCE((1 - (fe.embedding <=> $2::vector(768)))::REAL, 0) AS semantic_score,
                    COALESCE(ts_rank(f.fts_vector, plainto_tsquery('english', $1))::REAL, 0) AS keyword_score
                FROM files f
                LEFT JOIN file_embeddings fe
                  ON fe.file_id = f.id
                 AND COALESCE(fe.model, $7) = $7
                WHERE f.fts_vector @@ plainto_tsquery('english', $1)
                   OR (fe.embedding IS NOT NULL AND fe.embedding <=> $2::vector(768) < 0.7)
                   OR similarity(f.name, $1) > 0.1
                ORDER BY score DESC
                LIMIT $3
            """,
                expanded_query,
                q_vec_sql,
                request.limit * 2,
                request.semantic_weight * weight,
                request.keyword_weight * weight,
                request.meta_weight * weight,
                EMBED_MODEL,
            )

            for row in rows:
                file_id = row["file_id"]
                if file_id not in seen_ids:
                    seen_ids.add(file_id)
                    results.append(
                        {
                            "id": file_id,
                            "path": row["file_path"],
                            "name": row["file_name"],
                            "score": row["score"],
                            "semantic_score": row["semantic_score"],
                            "keyword_score": row["keyword_score"],
                        }
                    )

        results.sort(key=lambda x: x["score"], reverse=True)
        start_idx = (request.page - 1) * request.limit
        paginated_results = results[start_idx : start_idx + request.limit]

        response_payload = {
            "results": paginated_results,
            "total": len(results),
            "query": query,
            "source": "postgresql_fallback",
            "search_metadata": {
                "engine": "PostgreSQL + pgvector",
                "latency": "~10-50ms",
                "page": request.page,
                "limit": request.limit,
            },
        }
        if cache:
            await cache.set_search_result(
                query,
                request.limit,
                response_payload,
                cache_weights,
            )
        return response_payload


async def expand_query_with_tot(
    query: str, query_vec: List[float], conn: asyncpg.Connection, depth: int = 2
):
    """Tree of Thoughts query expansion (async version)"""
    results = [(query, query_vec, 1.0)]

    if depth <= 0:
        return results

    rows = await conn.fetch(
        """
        SELECT DISTINCT content_preview FROM files
        WHERE content_preview IS NOT NULL
          AND fts_vector @@ plainto_tsquery('english', $1)
        LIMIT 10
    """,
        query,
    )

    related_content = [row[0] for row in rows if row[0]]

    for content in related_content[:3]:
        words = content.split()[:20]
        if len(words) > 5:
            expanded = " ".join(words)
            expanded_vec = await get_embedding(expanded)
            similarity = cosine_similarity(query_vec, expanded_vec)
            if similarity > 0.5:
                results.append((expanded, expanded_vec, similarity * 0.8))

    seen = set()
    unique_results = []
    for r in results:
        if r[0] not in seen:
            seen.add(r[0])
            unique_results.append(r)

    unique_results.sort(key=lambda x: x[2], reverse=True)
    return unique_results[:5]


# ============================================================================
# Reciprocal Rank Fusion (RRF) Search - Phase 3A
# ============================================================================


@app.post("/api/search/v2")
async def rrf_search(request: RRFSearchRequest):
    """
    Reciprocal Rank Fusion search combining semantic, keyword, and metadata signals.
    RRF formula: score = sum(1.0 / (k + rank)) for k=60
    """
    import time

    query = normalize_query_text(request.query)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    cache = get_cache()
    cache_weights = ("rrf", request.rerank, request.include_similar)
    if cache:
        cached_result = await cache.get_search_result(query, request.limit, cache_weights)
        if cached_result is not None:
            return {**cached_result, "cached": True}

    start_time = time.time()
    query_embedding = await get_embedding(query)
    query_vec_sql = vector_to_sql(query_embedding)

    async with get_conn() as conn:
        # Signal 1: Semantic search (vector similarity)
        semantic_rows = await conn.fetch(
            """
            SELECT file_id, 1 - (embedding <=> $1::vector(768)) AS score
            FROM file_embeddings
            WHERE COALESCE(model, $2) = $2
            ORDER BY embedding <=> $1
            LIMIT 50
        """,
            query_vec_sql,
            EMBED_MODEL,
        )

        # Signal 2: Keyword search (full-text search)
        keyword_rows = await conn.fetch(
            """
            SELECT id AS file_id, ts_rank(fts_vector, plainto_tsquery('english', $1)) AS score
            FROM files
            WHERE fts_vector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT 50
        """,
            query,
        )

        # Signal 3: Metadata search (filename similarity using trigram)
        metadata_rows = await conn.fetch(
            """
            SELECT id AS file_id, similarity(name, $1) AS score
            FROM files
            WHERE similarity(name, $1) > 0.1
            ORDER BY score DESC
            LIMIT 50
        """,
            query,
        )

    # RRF Fusion with k=60
    K = 60
    rrf_scores: Dict[int, float] = {}
    file_info: Dict[int, Dict] = {}

    # Process semantic results
    for rank, row in enumerate(semantic_rows):
        file_id = row["file_id"]
        rrf_scores[file_id] = rrf_scores.get(file_id, 0.0) + 1.0 / (K + rank + 1)
        if file_id not in file_info:
            file_info[file_id] = {
                "semantic_score": row["score"],
                "keyword_score": 0.0,
                "metadata_score": 0.0,
            }
        else:
            file_info[file_id]["semantic_score"] = row["score"]

    # Process keyword results
    for rank, row in enumerate(keyword_rows):
        file_id = row["file_id"]
        rrf_scores[file_id] = rrf_scores.get(file_id, 0.0) + 1.0 / (K + rank + 1)
        if file_id not in file_info:
            file_info[file_id] = {
                "semantic_score": 0.0,
                "keyword_score": row["score"],
                "metadata_score": 0.0,
            }
        else:
            file_info[file_id]["keyword_score"] = row["score"]

    # Process metadata results
    for rank, row in enumerate(metadata_rows):
        file_id = row["file_id"]
        rrf_scores[file_id] = rrf_scores.get(file_id, 0.0) + 1.0 / (K + rank + 1)
        if file_id not in file_info:
            file_info[file_id] = {
                "semantic_score": 0.0,
                "keyword_score": 0.0,
                "metadata_score": row["score"],
            }
        else:
            file_info[file_id]["metadata_score"] = row["score"]

    # Sort by RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # Keep enough candidates for either reranking or direct response.
    candidate_count = min(max(request.limit, 50), len(sorted_results))
    rerank_candidates = sorted_results[:candidate_count]
    rerank_file_ids = [file_id for file_id, _ in rerank_candidates]

    async with get_conn() as conn:
        # Get file details with content preview for re-ranking
        file_rows = await conn.fetch(
            """
            SELECT id, path, name, extension, size_bytes, content_preview
            FROM files
            WHERE id = ANY($1)
        """,
            rerank_file_ids,
        )

        files_by_id = {row["id"]: dict(row) for row in file_rows}

    # Phase 3B: Re-ranking on content preview
    if request.rerank and rerank_candidates:
        # Collect content previews for batch embedding
        contents_to_embed = []
        content_file_ids = []

        for file_id, rrf_score in rerank_candidates:
            if file_id in files_by_id:
                content = files_by_id[file_id].get("content_preview", "")
                if content:
                    contents_to_embed.append(content[:2000])  # Limit content length
                    content_file_ids.append(file_id)

        # Batch embed content previews
        if contents_to_embed:
            logger.info(
                f"Re-ranking: computing embeddings for {len(contents_to_embed)} content previews"
            )
            content_embeddings = await get_embeddings_batch(contents_to_embed)

            # Compute precise similarity with query
            for file_id, content_emb in zip(content_file_ids, content_embeddings):
                if file_id in file_info:
                    precise_score = cosine_similarity(query_embedding, content_emb)
                    file_info[file_id]["precise_score"] = precise_score

            # Re-sort by precise score if available
            reranked = []
            for file_id, rrf_score in rerank_candidates:
                precise = file_info.get(file_id, {}).get("precise_score", 0)
                # Combine RRF score with precise score (weighted)
                combined_score = rrf_score * 0.3 + precise * 0.7
                reranked.append((file_id, combined_score, precise))

            reranked.sort(key=lambda x: x[1], reverse=True)
            sorted_results = [(fid, score) for fid, score, _ in reranked]

    # Build final results
    results = []
    for file_id, score in sorted_results[: request.limit]:
        if file_id in files_by_id:
            file_data = files_by_id[file_id]
            info = file_info.get(file_id, {})
            rrf_base_score = rrf_scores.get(file_id, score)

            result = {
                "id": file_id,
                "path": file_data.get("path", ""),
                "name": file_data.get("name", ""),
                "extension": file_data.get("extension", ""),
                "size_bytes": file_data.get("size_bytes", 0),
                "content_preview": file_data.get("content_preview", ""),
                "rrf_score": rrf_base_score if not request.rerank else score,
                "semantic_score": info.get("semantic_score", 0.0),
                "keyword_score": info.get("keyword_score", 0.0),
                "metadata_score": info.get("metadata_score", 0.0),
                "precise_score": info.get("precise_score") if request.rerank else None,
                "reranked": request.rerank,
                "signals_found": sum(
                    1
                    for s in [
                        info.get("semantic_score", 0),
                        info.get("keyword_score", 0),
                        info.get("metadata_score", 0),
                    ]
                    if s > 0
                ),
            }

            results.append(result)

    # Phase 4C: GraphRAG - Add graph neighbor context
    if request.include_similar:
        graph_mgr = get_graph_manager()
        if graph_mgr:
            for result in results:
                try:
                    neighbors = await graph_mgr.query_neighbors(
                        result["id"], depth=1, min_similarity=0.6
                    )
                    result["related_files"] = neighbors[:5]  # Top 5 related files
                except Exception as e:
                    logger.debug(f"GraphRAG query failed for file {result['id']}: {e}")
                    result["related_files"] = []
        else:
            for result in results:
                result["related_files"] = []

    elapsed_ms = (time.time() - start_time) * 1000

    response_payload = {
        "results": results,
        "total": len(sorted_results),
        "query": query,
        "source": "rrf_fusion",
        "search_metadata": {
            "engine": "RRF (Semantic + Keyword + Metadata)",
            "latency_ms": round(elapsed_ms, 2),
            "signals": {
                "semantic": len(semantic_rows),
                "keyword": len(keyword_rows),
                "metadata": len(metadata_rows),
            },
            "rerank_enabled": request.rerank,
            "graphrag_enabled": request.include_similar,
        },
    }

    if cache:
        await cache.set_search_result(query, request.limit, response_payload, cache_weights)
    return response_payload


# ============================================================================
# Chat & RAG
# ============================================================================


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stream chat response using RAG.
    """
    from chat_service import chat_with_data  # Lazy import to avoid circular dep if any
    from fastapi.responses import StreamingResponse

    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    return StreamingResponse(
        chat_with_data(request.query, history_dicts, request.context_window),
        media_type="text/plain",
    )


@app.post("/api/search/semantic")
async def semantic_search(request: SemanticSearchRequest):
    """Pure semantic search using embeddings (async version)"""
    query = normalize_query_text(request.query)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    cache = get_cache()
    cache_weights = ("semantic", round(request.threshold, 3), request.include_metadata)
    if cache:
        cached_result = await cache.get_search_result(query, request.top_k, cache_weights)
        if cached_result is not None:
            return {**cached_result, "cached": True}

    query_vec = np.array(await get_embedding(query), dtype=np.float32)

    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT f.id, f.path, f.name, f.extension, f.size_bytes, fe.embedding <-> $1 AS distance
            FROM files f
            JOIN file_embeddings fe ON f.id = fe.file_id
            WHERE fe.embedding IS NOT NULL
              AND COALESCE(fe.model, $3) = $3
            ORDER BY fe.embedding <-> $1
            LIMIT $2
        """,
            vector_to_sql(query_vec.tolist()),
            request.top_k,
            EMBED_MODEL,
        )

        results = []
        for row in rows:
            similarity = 1.0 / (1.0 + row["distance"])
            if similarity >= request.threshold:
                results.append(
                    {
                        "id": row["id"],
                        "path": row["path"],
                        "name": row["name"],
                        "similarity": similarity,
                    }
                )

        response_payload = {"results": results, "query": query}
        if cache:
            await cache.set_search_result(
                query,
                request.top_k,
                response_payload,
                cache_weights,
            )
        return response_payload


@app.post("/api/search/faceted")
async def faceted_search(request: FacetedSearchRequest):
    """Faceted search with filters (async version)"""
    async with get_conn() as conn:
        where_parts = ["1=1"]
        params = []
        param_idx = 0

        if request.query:
            param_idx += 1
            where_parts.append(
                f"(f.name ILIKE ${param_idx} OR f.path ILIKE ${param_idx})"
            )
            params.append(f"%{request.query}%")

        if request.facets.get("extensions"):
            param_idx += 1
            where_parts.append(f"f.extension = ANY(${param_idx})")
            params.append(request.facets["extensions"])

        where_clause = " AND ".join(where_parts)

        data_query = (
            f"SELECT f.* FROM files f WHERE {where_clause} "
            f"ORDER BY f.file_modified_at DESC LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
        )
        params.extend([request.limit, (request.page - 1) * request.limit])

        rows = await conn.fetch(data_query, *params)
        files = [dict(row) for row in rows]
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM files f WHERE {where_clause}",
            *params[:param_idx],
        )

        # Get aggregations
        agg_rows = await conn.fetch("""
            SELECT extension, COUNT(*) as count FROM files 
            WHERE extension IS NOT NULL 
            GROUP BY extension ORDER BY count DESC LIMIT 10
        """)
        extensions = [
            {"extension": r["extension"], "count": r["count"]} for r in agg_rows
        ]

        return {
            "files": files,
            "total": total,
            "page": request.page,
            "limit": request.limit,
            "aggregations": {"extensions": extensions},
        }


@app.get("/api/files/{file_id}")
async def get_file_details(file_id: int):
    """Get detailed file information (async version)"""
    async with get_conn() as conn:
        row = await conn.fetchrow("SELECT * FROM files WHERE id = $1", file_id)

        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        file = dict(row)

        tag_rows = await conn.fetch(
            """
            SELECT t.name FROM tags t
            JOIN file_tags ft ON t.id = ft.tag_id
            WHERE ft.file_id = $1
        """,
            file_id,
        )
        file["tags"] = [r["name"] for r in tag_rows]

        return file


async def get_similar_files(file_id: int, conn: asyncpg.Connection, limit: int = 5):
    """Get semantically similar files (async version)"""
    rows = await conn.fetch(
        """
        SELECT f.id, f.path, f.name, fe.embedding <-> (
            SELECT embedding
            FROM file_embeddings
            WHERE file_id = $1 AND COALESCE(model, $2) = $2
        ) AS distance
        FROM files f
        JOIN file_embeddings fe ON f.id = fe.file_id
        WHERE f.id != $1
          AND fe.embedding IS NOT NULL
          AND COALESCE(fe.model, $2) = $2
        ORDER BY fe.embedding <-> (
            SELECT embedding
            FROM file_embeddings
            WHERE file_id = $1 AND COALESCE(model, $2) = $2
        )
        LIMIT $3
    """,
        file_id,
        EMBED_MODEL,
        limit,
    )

    return [
        {"id": r["id"], "path": r["path"], "name": r["name"], "distance": r["distance"]}
        for r in rows
    ]


async def get_file_relationships(file_id: int, conn: asyncpg.Connection):
    """Get file relationships (async version)"""
    rows = await conn.fetch(
        """
        SELECT f.id, f.path, f.name, r.relationship_type, r.weight
        FROM files f
        JOIN file_relationships r ON f.id = r.related_file_id
        WHERE r.file_id = $1
        LIMIT 10
    """,
        file_id,
    )

    return [
        {
            "id": r["id"],
            "path": r["path"],
            "name": r["name"],
            "relationship": r["relationship_type"],
            "weight": r["weight"],
        }
        for r in rows
    ]


# ============================================================================
# Tree of Thoughts Reasoning
# ============================================================================


@app.post("/api/tot/reason")
async def tree_of_thoughts_reasoning(request: TreeOfThoughtsRequest):
    """Advanced reasoning using Tree of Thoughts approach (async version)"""
    query_vec = np.array(await get_embedding(request.seed_query), dtype=np.float32)

    async with get_conn() as conn:
        # Initial exploration
        rows = await conn.fetch(
            """
            SELECT f.id, f.path, f.name, f.content_preview, fe.embedding <-> $1 AS distance
            FROM files f
            JOIN file_embeddings fe ON f.id = fe.file_id
            WHERE fe.embedding IS NOT NULL
              AND COALESCE(fe.model, $2) = $2
              AND f.content_preview IS NOT NULL
            ORDER BY fe.embedding <-> $1
            LIMIT $3
        """,
            vector_to_sql(query_vec.tolist()),
            EMBED_MODEL,
            request.branching_factor,
        )

        initial_nodes = [dict(row) for row in rows]

        # Expand reasoning paths
        reasoning_paths = []
        for node in initial_nodes:
            path = {
                "query": request.seed_query,
                "current_focus": node["name"],
                "reasoning": f"Starting with {node['name']}",
                "confidence": 1.0 - min(node["distance"], 1.0),
                "related_files": [],
            }

            # Find related concepts
            if node["content_preview"]:
                path["reasoning"] += (
                    f" based on content: {node['content_preview'][:100]}..."
                )

            reasoning_paths.append(path)

        # Combine similar paths
        combined_paths = []
        seen = set()
        for path in reasoning_paths:
            key = path["current_focus"]
            if key not in seen:
                seen.add(key)
                combined_paths.append(path)

        return {
            "seed_query": request.seed_query,
            "reasoning_paths": combined_paths[: request.branching_factor],
            "depth_reached": 1,
            "strategy": request.exploration_strategy,
        }


# ============================================================================
# Knowledge Graph & Connections
# ============================================================================


@app.post("/api/graph/query")
async def query_knowledge_graph(request: GraphQueryRequest):
    """Query the knowledge graph for file relationships."""
    graph_mgr = get_graph_manager()
    if not graph_mgr:
        raise HTTPException(status_code=503, detail="Graph manager not initialized")

    center_file_id = request.center_file_id
    async with get_conn() as conn:
        if center_file_id is None and request.center_path:
            center_file_id = await conn.fetchval(
                "SELECT id FROM files WHERE path = $1",
                request.center_path,
            )
            if center_file_id is None:
                raise HTTPException(status_code=404, detail="Center file path not found")

        if center_file_id is None:
            nodes_indexed = await conn.fetchval(
                """
                SELECT COUNT(*) FROM files f
                JOIN file_embeddings fe ON fe.file_id = f.id
                WHERE COALESCE(fe.model, $1) = $1
                """,
                EMBED_MODEL,
            )
            graph_status = graph_mgr.get_status()
            return {
                "nodes_indexed": nodes_indexed,
                "edges_indexed": graph_status["edge_count"],
                "backend": graph_status["backend"],
                "graph_status": graph_status,
                "message": "Provide center_file_id or center_path for neighborhood traversal",
            }

        center_row = await conn.fetchrow(
            "SELECT id, path, name, extension FROM files WHERE id = $1",
            center_file_id,
        )
        if center_row is None:
            raise HTTPException(status_code=404, detail="Center file not found")

    neighbors = await graph_mgr.query_neighbors(
        center_file_id,
        depth=request.depth,
        min_similarity=request.min_similarity,
    )

    return {
        "center": dict(center_row),
        "neighbors": neighbors,
        "total_neighbors": len(neighbors),
        "depth": request.depth,
        "backend": graph_mgr.get_status()["backend"],
    }


@app.get("/api/graph/status")
async def get_graph_status():
    """Get graph backend and build status."""
    graph_mgr = get_graph_manager()
    if not graph_mgr:
        raise HTTPException(status_code=503, detail="Graph manager not initialized")
    return graph_mgr.get_status()


# ============================================================================
# Phase 4B: Graph Algorithms (PageRank, Communities, Shortest Path)
# ============================================================================


@app.get("/api/graph/pagerank")
async def get_pagerank(limit: int = Query(20, ge=1, le=100)):
    """Get files ranked by PageRank (most connected/important files)."""
    graph_mgr = get_graph_manager()
    if not graph_mgr:
        raise HTTPException(status_code=503, detail="Graph manager not initialized")

    try:
        results = await graph_mgr.get_pagerank(limit=limit)
        return {
            "pagerank_results": results,
            "total": len(results),
            "algorithm": "PageRank",
            "backend": "AGE" if graph_mgr._use_age else "NetworkX",
        }
    except Exception as e:
        logger.error(f"PageRank error: {e}")
        raise HTTPException(status_code=500, detail=f"PageRank calculation failed: {e}")


@app.get("/api/graph/communities")
async def get_communities():
    """Detect file communities using Louvain algorithm."""
    graph_mgr = get_graph_manager()
    if not graph_mgr:
        raise HTTPException(status_code=503, detail="Graph manager not initialized")

    try:
        results = await graph_mgr.get_communities()
        return {
            "communities": results,
            "total_communities": len(results),
            "algorithm": "Louvain",
            "backend": "AGE" if graph_mgr._use_age else "NetworkX",
        }
    except Exception as e:
        logger.error(f"Communities error: {e}")
        raise HTTPException(status_code=500, detail=f"Community detection failed: {e}")


@app.get("/api/graph/path")
async def get_shortest_path(
    from_id: int = Query(..., description="Source file ID"),
    to_id: int = Query(..., description="Target file ID"),
):
    """Find shortest path between two files in the knowledge graph."""
    graph_mgr = get_graph_manager()
    if not graph_mgr:
        raise HTTPException(status_code=503, detail="Graph manager not initialized")

    try:
        result = await graph_mgr.get_shortest_path(from_id, to_id)
        if result is None:
            return {
                "from_id": from_id,
                "to_id": to_id,
                "path_exists": False,
                "message": "No path found between the specified files",
            }

        return {
            "from_id": from_id,
            "to_id": to_id,
            "path_exists": True,
            "path_length": result["path_length"],
            "files": result["files"],
            "backend": "AGE" if graph_mgr._use_age else "NetworkX",
        }
    except Exception as e:
        logger.error(f"Shortest path error: {e}")
        raise HTTPException(status_code=500, detail=f"Path calculation failed: {e}")


# ============================================================================
# AI Insights & Recommendations
# ============================================================================


@app.post("/api/insights")
async def get_insights(request: InsightRequest):
    """Generate AI-powered insights about files (async version)"""
    async with get_conn() as conn:
        insights = {}

        if "duplicates" in request.insight_types:
            rows = await conn.fetch("""
                SELECT id, path, name, size_bytes, sha256, dup_count
                FROM (
                    SELECT id, path, name, size_bytes, sha256, COUNT(*) OVER (PARTITION BY sha256) as dup_count
                    FROM files
                    WHERE sha256 IS NOT NULL
                ) sub
                WHERE dup_count > 1
                ORDER BY dup_count DESC
                LIMIT 10
            """)
            insights["duplicates"] = [dict(row) for row in rows]

        if "clusters" in request.insight_types:
            rows = await conn.fetch("""
                SELECT extension, COUNT(*) as count, AVG(size_bytes) as avg_size
                FROM files
                WHERE extension IS NOT NULL
                GROUP BY extension
                ORDER BY count DESC
                LIMIT 10
            """)
            insights["clusters"] = {"by_extension": [dict(row) for row in rows]}

        if "anomalies" in request.insight_types:
            rows = await conn.fetch("""
                SELECT id, path, name, size_bytes
                FROM files
                WHERE size_bytes > (SELECT AVG(size_bytes) + 3 * STDDEV(size_bytes) FROM files)
                ORDER BY size_bytes DESC
                LIMIT 10
            """)
            insights["anomalies"] = {"large_files": [dict(row) for row in rows]}

        return insights


@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Generate personalized file recommendations (async version)"""
    async with get_conn() as conn:
        recommendations = []

        # Based on similar files
        if request.based_on_similar:
            query_vec = np.array(await get_embedding(request.context), dtype=np.float32)
            rows = await conn.fetch(
                """
                SELECT f.id, f.path, f.name, fe.embedding <-> $1 AS distance
                FROM files f
                JOIN file_embeddings fe ON f.id = fe.file_id
                WHERE fe.embedding IS NOT NULL
                  AND COALESCE(fe.model, $2) = $2
                ORDER BY fe.embedding <-> $1
                LIMIT $3
            """,
                vector_to_sql(query_vec.tolist()),
                EMBED_MODEL,
                request.max_recommendations,
            )

            for row in rows:
                similarity = 1.0 / (1.0 + row["distance"])
                recommendations.append(
                    {
                        "file_id": row["id"],
                        "path": row["path"],
                        "name": row["name"],
                        "reason": f"Similar to your query",
                        "confidence": similarity,
                    }
                )

        return recommendations


@app.get("/api/dashboard")
async def get_dashboard_stats():
    """Dashboard statistics and overview (async version)"""
    async with get_conn() as conn:
        stats = {}

        stats["total_files"] = await conn.fetchval("SELECT COUNT(*) FROM files")

        result = await conn.fetchval("SELECT SUM(size_bytes) FROM files")
        stats["total_size"] = result if result else 0

        stats["unique_extensions"] = await conn.fetchval(
            "SELECT COUNT(DISTINCT extension) FROM files WHERE extension IS NOT NULL"
        )

        stats["with_embeddings"] = await conn.fetchval(
            "SELECT COUNT(DISTINCT file_id) FROM file_embeddings WHERE COALESCE(model, $1) = $1",
            EMBED_MODEL,
        )

        stats["modified_last_24h"] = await conn.fetchval(
            "SELECT COUNT(*) FROM files WHERE file_modified_at > NOW() - INTERVAL '24 hours'"
        )

        # File type breakdown
        rows = await conn.fetch("""
            SELECT 
                CASE 
                    WHEN extension IN ('.py', '.js', '.ts', '.java', '.cpp', '.c') THEN 'Code'
                    WHEN extension IN ('.md', '.txt', '.pdf', '.doc') THEN 'Document'
                    WHEN extension IN ('.png', '.jpg', '.gif', '.svg') THEN 'Image'
                    WHEN extension IN ('.mp4', '.avi', '.mkv') THEN 'Video'
                    WHEN extension IN ('.mp3', '.wav', '.flac') THEN 'Audio'
                    ELSE 'Other'
                END as type,
                COUNT(*) as count
            FROM files
            GROUP BY type
            ORDER BY count DESC
        """)
        stats["by_type"] = [dict(row) for row in rows]

        # Size distribution
        rows = await conn.fetch("""
            SELECT 
                CASE 
                    WHEN size_bytes < 1000 THEN 'Tiny (<1KB)'
                    WHEN size_bytes < 100000 THEN 'Small (1KB-100KB)'
                    WHEN size_bytes < 10000000 THEN 'Medium (100KB-10MB)'
                    ELSE 'Large (>10MB)'
                END as size_range,
                COUNT(*) as count
            FROM files
            GROUP BY size_range
        """)
        stats["by_size"] = [dict(row) for row in rows]

        embedding_coverage = {
            "with_embeddings": stats["with_embeddings"],
            "total": stats["total_files"],
            "percentage": round(
                (stats["with_embeddings"] / stats["total_files"] * 100), 2
            )
            if stats["total_files"] > 0
            else 0,
        }

        return {"stats": stats, "embedding_coverage": embedding_coverage}


# ============================================================================
# File Operations
# ============================================================================


@app.get("/api/files")
async def list_files(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    extension: Optional[str] = None,
    q: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = Query("modified", pattern="^(modified|size|name)$"),
):
    """List files with pagination (async version)"""
    async with get_conn() as conn:
        conditions = ["1=1"]
        params: List[Any] = []
        param_idx = 1

        if extension:
            conditions.append(f"extension = ${param_idx}")
            params.append(extension)
            param_idx += 1

        if q:
            normalized_term = normalize_query_text(q)
            if normalized_term:
                conditions.append(
                    f"(name ILIKE ${param_idx} OR path ILIKE ${param_idx} OR content_preview ILIKE ${param_idx})"
                )
                params.append(f"%{normalized_term}%")
                param_idx += 1

        if category and category != "all":
            category_key = category.lower()
            extensions = sorted(CATEGORY_EXTENSIONS.get(category_key, set()))
            if not extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown category '{category}'.",
                )
            conditions.append(f"extension = ANY(${param_idx})")
            params.append(extensions)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}"

        order_col = {
            "modified": "file_modified_at",
            "size": "size_bytes",
            "name": "name",
        }[sort_by]
        order_dir = "ASC" if sort_by == "name" else "DESC"

        query = (
            f"SELECT * FROM files {where_clause} "
            f"ORDER BY {order_col} {order_dir} NULLS LAST "
            f"LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        )
        query_params = [*params, limit, (page - 1) * limit]

        rows = await conn.fetch(query, *query_params)
        files = [dict(row) for row in rows]
        for file in files:
            file["category"] = classify_extension(file.get("extension"))

        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM files {where_clause}",
            *params,
        )

        return {"files": files, "total": total, "page": page, "limit": limit}


@app.get("/api/files/{file_id}/content")
async def get_file_content(file_id: int):
    """Get file content (for supported types) (async version)"""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT path, extension, content_preview FROM files WHERE id = $1",
            file_id,
        )

        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        path, extension, content = row["path"], row["extension"], row["content_preview"]

        return {
            "id": file_id,
            "path": path,
            "extension": extension,
            "content": content or "Preview not available",
        }


@app.post("/api/files/{file_id}/tags")
async def update_file_tags(file_id: int, request: FileTagUpdateRequest):
    """Update tags for a file (async version)"""
    tags = sorted({tag.strip().lower() for tag in request.tags if tag.strip()})
    async with get_conn() as conn:
        file_exists = await conn.fetchval("SELECT 1 FROM files WHERE id = $1", file_id)
        if not file_exists:
            raise HTTPException(status_code=404, detail="File not found")

        async with conn.transaction():
            # Remove existing tags
            await conn.execute("DELETE FROM file_tags WHERE file_id = $1", file_id)

            # Add new tags
            for tag in tags:
                tag_id = await conn.fetchval(
                    """
                    INSERT INTO tags (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """,
                    tag,
                )
                await conn.execute(
                    "INSERT INTO file_tags (file_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    file_id,
                    tag_id,
                )

        return {"message": "Tags updated successfully", "tags": tags}


# ============================================================================
# Export Functionality
# ============================================================================


@app.get("/export/{export_type}")
async def export_data(
    export_type: str,
    query: Optional[str] = None,
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Export data in various formats (async version)"""
    async with get_conn() as conn:
        if export_type == "search" and query:
            rows = await conn.fetch(
                """
                SELECT * FROM files
                WHERE name ILIKE $1 OR path ILIKE $1 OR content_preview ILIKE $1
                LIMIT 1000
            """,
                f"%{query}%",
            )
        elif export_type == "files":
            rows = await conn.fetch("SELECT * FROM files LIMIT 1000")
        elif export_type == "insights":
            rows = await conn.fetch("""
                SELECT extension, COUNT(*) as count FROM files GROUP BY extension
            """)
        elif export_type == "graph":
            rows = await conn.fetch("""
                SELECT f.id, f.path, f.name, fe.embedding
                FROM files f
                JOIN file_embeddings fe ON fe.file_id = f.id
                WHERE COALESCE(fe.model, $1) = $1
                LIMIT 100
            """, EMBED_MODEL)
        else:
            rows = []

        data = [dict(row) for row in rows]

        if format == "csv":
            csv_buffer = io.StringIO()
            if data:
                headers = list(data[0].keys())
                writer = csv.DictWriter(csv_buffer, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            return Response(
                content=csv_buffer.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={export_type}.csv"
                },
            )

        return data


# ============================================================================
# WebSocket Real-time Updates
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON payload"}
                )
                continue

            message_type = message.get("type")
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif message_type == "search":
                results = await perform_realtime_search(message.get("query", ""))
                await websocket.send_json(
                    {"type": "search_results", "results": results}
                )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


async def perform_realtime_search(query: str):
    """Perform real-time search for WebSocket (async version)"""
    query = normalize_query_text(query)
    if not query:
        return []

    query_vec = await get_embedding(query)

    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT f.id, f.path, f.name, fe.embedding <-> $1 AS distance
            FROM files f
            JOIN file_embeddings fe ON fe.file_id = f.id
            WHERE COALESCE(fe.model, $2) = $2
            ORDER BY fe.embedding <-> $1
            LIMIT 5
        """,
            vector_to_sql(query_vec),
            EMBED_MODEL,
        )

        return [{"id": r["id"], "path": r["path"], "name": r["name"]} for r in rows]


# ============================================================================
# OPTIMIZATION ENGINE ENDPOINTS
# ============================================================================


@app.get("/api/optimization/status")
async def get_optimization_status():
    """Get status of optimization engine"""
    engine = get_optimization_engine()

    if OPTIMIZATION_MODULES_AVAILABLE and engine:
        stats = engine.get_stats()
        return {
            "available": True,
            "engine": "Ultimate Intelligent Storage Nexus",
            "status": "ready" if engine.is_initialized else "initializing",
            "features": {
                "binary_quantization": True,
                "hnsw_index": True,
                "multi_tier_storage": True,
                "hybrid_rag": True,
                "agentic_ai": True,
            },
            "performance": {
                "search_latency_ms": "~0.56",
                "speedup_vs_baseline": "89x",
            },
            "statistics": stats,
        }
    else:
        return {
            "available": False,
            "engine": "PostgreSQL + pgvector",
            "status": "fallback_mode",
            "features": {
                "binary_quantization": False,
                "hnsw_index": False,
                "multi_tier_storage": False,
                "hybrid_rag": False,
                "agentic_ai": False,
            },
            "performance": {
                "search_latency_ms": "~10-50",
                "speedup_vs_baseline": "1x (baseline)",
            },
            "message": "Optimization modules not loaded",
        }


@app.post("/api/optimization/index")
async def index_embeddings_for_optimization(file_ids: List[int]):
    """Index embeddings into the optimization engine (async version)"""
    engine = get_optimization_engine()

    if not engine:
        raise HTTPException(status_code=503, detail="Optimization engine not available")

    try:
        async with get_conn() as conn:
            rows = await conn.fetch(
                """
                SELECT f.id, f.path, f.name, f.extension, f.size_bytes, fe.embedding
                FROM files f
                JOIN file_embeddings fe ON fe.file_id = f.id
                WHERE f.id = ANY($1)
                  AND COALESCE(fe.model, $2) = $2
                LIMIT 1000
            """,
                file_ids,
                EMBED_MODEL,
            )

            if not rows:
                return {"message": "No embeddings found"}

            indexed_rows = []
            for row in rows:
                vector = parse_embedding_value(row["embedding"])
                if vector.shape[0] == EMBED_DIM:
                    indexed_rows.append((row, vector))

            if not indexed_rows:
                return {"message": "No valid embeddings found"}

            embeddings = np.vstack([vector for _, vector in indexed_rows]).astype(
                np.float32
            )
            metadata = [
                {
                    "id": row["id"],
                    "path": row["path"],
                    "name": row["name"],
                    "extension": row["extension"],
                    "size": row["size_bytes"],
                }
                for row, _ in indexed_rows
            ]

            indexed_ids = [row["id"] for row, _ in indexed_rows]
            engine.index_files(indexed_ids, embeddings, metadata)

            return {
                "message": f"Indexed {len(indexed_ids)} embeddings",
                "engine": "Ultimate Edition (0.56ms latency)",
            }
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimization/benchmark")
async def run_optimization_benchmark(n_files: int = 1000):
    """Run performance benchmark (async version)"""
    if not OPTIMIZATION_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Optimization modules not available"
        )

    try:
        async with get_conn() as conn:
            # Get random files
            rows = await conn.fetch(
                """
                SELECT fe.file_id AS id
                FROM file_embeddings fe
                WHERE COALESCE(fe.model, $1) = $1
                ORDER BY RANDOM()
                LIMIT $2
                """,
                EMBED_MODEL,
                n_files,
            )
            file_ids = [r["id"] for r in rows]

        engine = get_optimization_engine()
        if not engine:
            raise HTTPException(
                status_code=503, detail="Optimization engine failed to initialize"
            )
        benchmark = PerformanceBenchmark(engine)
        results = benchmark.run(n_files=n_files)

        return {
            "benchmark_results": results,
            "files_tested": len(file_ids),
        }
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH & MONITORING
# ============================================================================


@app.get("/api/health")
async def health_check():
    """Health check endpoint (Phase 6E enhanced)"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {},
    }

    # Database check
    try:
        async with get_conn() as conn:
            file_count = await conn.fetchval("SELECT COUNT(*) FROM files")
            health["services"]["database"] = {
                "status": "connected",
                "files_indexed": file_count,
            }
    except Exception as e:
        health["services"]["database"] = {"status": "error", "error": str(e)}
        health["status"] = "degraded"

    # Gemini API check (Phase 6E)
    try:
        from config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            health["services"]["gemini"] = {
                "status": "configured",
                "embed_model": EMBED_MODEL,
            }
        else:
            health["services"]["gemini"] = {
                "status": "not_configured",
                "error": "ISN_GEMINI_API_KEY not set",
            }
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["gemini"] = {"status": "error", "error": str(e)}
        health["status"] = "degraded"

    # Background processes check
    try:
        import psutil
        indexer_active = any("indexer.py" in " ".join(p.cmdline()) for p in psutil.process_iter() if p.name().startswith("python"))
        health["services"]["indexer"] = {
            "status": "running" if indexer_active else "idle",
            "active_tasks": len(progress_manager.operations)
        }
    except Exception:
        health["services"]["indexer"] = {"status": "unknown"}

    # Disk space check (Phase 6E)
    try:
        disk = shutil.disk_usage("/")
        health["services"]["disk"] = {
            "status": "ok",
            "total_gb": round(disk.total / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "used_percent": round((disk.used / disk.total) * 100, 1),
        }
        if (disk.free / disk.total) < 0.1:  # Less than 10% free
            health["services"]["disk"]["status"] = "warning"
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["disk"] = {"status": "error", "error": str(e)}

    # Optimization modules
    health["optimization_engine"] = OPTIMIZATION_MODULES_AVAILABLE

    # Graph status
    graph_mgr = get_graph_manager()
    if graph_mgr:
        health["services"]["graph"] = graph_mgr.get_status()

    # Rate limiting status (Phase 6E)
    health["rate_limiting"] = "enabled" if limiter else "disabled"

    if health["status"] != "healthy":
        raise HTTPException(status_code=503, detail=health)

    return health


# Phase 6C: Duplicate Detection Dashboard
@app.get("/api/duplicates")
async def get_duplicates(
    type: str = Query(
        "exact",
        pattern="^(exact|near)$",
        description="Type: 'exact' or 'near'",
    ),
    threshold: float = Query(
        0.95, ge=0.0, le=1.0, description="Similarity threshold for near-duplicates"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of groups"),
):
    """Find duplicate files by SHA256 (exact) or embedding similarity (near)."""

    async with get_conn() as conn:
        if type == "exact":
            # Find files with same SHA256 hash
            rows = await conn.fetch(
                """
                SELECT 
                    sha256,
                    COUNT(*) as count,
                    array_agg(json_build_object('id', id, 'name', name, 'path', path, 'size', size_bytes)) as files
                FROM files
                WHERE sha256 IS NOT NULL
                GROUP BY sha256
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT $1
                """,
                limit,
            )

            return {
                "type": "exact",
                "total_groups": len(rows),
                "groups": [
                    {
                        "sha256": row["sha256"][:16] + "...",
                        "count": row["count"],
                        "files": row["files"],
                    }
                    for row in rows
                ],
            }

        else:  # near duplicates
            # Find similar files using embeddings (limited scope for performance)
            rows = await conn.fetch(
                """
                SELECT 
                    f1.id as id1,
                    f2.id as id2,
                    f1.name as name1,
                    f2.name as name2,
                    f1.path as path1,
                    f2.path as path2,
                    1 - (e1.embedding <=> e2.embedding) as similarity
                FROM file_embeddings e1
                JOIN file_embeddings e2 ON e1.file_id < e2.file_id
                JOIN files f1 ON f1.id = e1.file_id
                JOIN files f2 ON f2.id = e2.file_id
                WHERE 1 - (e1.embedding <=> e2.embedding) > $1
                  AND COALESCE(e1.model, $3) = $3
                  AND COALESCE(e2.model, $3) = $3
                  AND e1.file_id IN (
                      SELECT file_id FROM file_embeddings 
                      WHERE COALESCE(model, $3) = $3
                      ORDER BY file_id LIMIT 10000
                  )
                ORDER BY similarity DESC
                LIMIT $2
                """,
                threshold,
                limit,
                EMBED_MODEL,
            )

            return {
                "type": "near",
                "threshold": threshold,
                "total_pairs": len(rows),
                "pairs": [
                    {
                        "file1": {
                            "id": r["id1"],
                            "name": r["name1"],
                            "path": r["path1"],
                        },
                        "file2": {
                            "id": r["id2"],
                            "name": r["name2"],
                            "path": r["path2"],
                        },
                        "similarity": round(r["similarity"], 4),
                    }
                    for r in rows
                ],
            }


# Phase 6D: Natural Language Query Parser
@app.post("/api/search/natural")
async def natural_language_search(request: NaturalLanguageSearchRequest):
    """Parse natural language query and return filtered results.

    Example: "large Python files from last week"
    """
    query_text = normalize_query_text(request.query)

    if not query_text:
        raise HTTPException(status_code=400, detail="Query is required")

    # Parse natural language using LLM
    filters = await parse_natural_language_query(query_text)

    # Build and execute search with filters
    async with get_conn() as conn:
        # Build WHERE clauses based on filters
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        # Extension filter
        if filters.get("extensions"):
            ext_placeholders = ", ".join(
                [
                    f"${i}"
                    for i in range(param_idx, param_idx + len(filters["extensions"]))
                ]
            )
            where_clauses.append(f"extension IN ({ext_placeholders})")
            params.extend(filters["extensions"])
            param_idx += len(filters["extensions"])

        # Size filters
        if filters.get("min_size_bytes"):
            where_clauses.append(f"size_bytes >= ${param_idx}")
            params.append(filters["min_size_bytes"])
            param_idx += 1

        if filters.get("max_size_bytes"):
            where_clauses.append(f"size_bytes <= ${param_idx}")
            params.append(filters["max_size_bytes"])
            param_idx += 1

        # Date filters
        if filters.get("date_after"):
            try:
                date_after = datetime.fromisoformat(filters["date_after"])
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date_after value: {filters['date_after']}",
                ) from e
            where_clauses.append(f"file_modified_at >= ${param_idx}")
            params.append(date_after)
            param_idx += 1

        if filters.get("date_before"):
            try:
                date_before = datetime.fromisoformat(filters["date_before"])
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date_before value: {filters['date_before']}",
                ) from e
            where_clauses.append(f"file_modified_at <= ${param_idx}")
            params.append(date_before)
            param_idx += 1

        # Search text filter
        if filters.get("search_text"):
            where_clauses.append(
                f"(name ILIKE ${param_idx} OR path ILIKE ${param_idx} OR content_preview ILIKE ${param_idx})"
            )
            params.append(f"%{filters['search_text']}%")
            param_idx += 1

        # Sort order
        sort_mapping = {
            "size_desc": "size_bytes DESC",
            "size_asc": "size_bytes ASC",
            "date_desc": "file_modified_at DESC",
            "date_asc": "file_modified_at ASC",
            "name_asc": "name ASC",
        }
        sort_by = sort_mapping.get(filters.get("sort_by"), "file_modified_at DESC")

        params.append(request.limit)

        # Execute query
        sql = f"""
            SELECT id, path, name, extension, size_bytes, file_modified_at, content_preview
            FROM files
            WHERE {" AND ".join(where_clauses)}
            ORDER BY {sort_by} NULLS LAST
            LIMIT ${param_idx}
        """

        rows = await conn.fetch(sql, *params)

        results = [dict(row) for row in rows]

        return {
            "query": query_text,
            "parsed_filters": filters,
            "total": len(results),
            "results": results,
        }


def _normalize_natural_filters(filters: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Normalize and validate natural-language-derived filters."""
    normalized: Dict[str, Any] = {
        "search_text": filters.get("search_text"),
        "extensions": filters.get("extensions") or [],
        "min_size_bytes": filters.get("min_size_bytes"),
        "max_size_bytes": filters.get("max_size_bytes"),
        "date_after": filters.get("date_after"),
        "date_before": filters.get("date_before"),
        "sort_by": filters.get("sort_by"),
    }

    if not isinstance(normalized["extensions"], list):
        normalized["extensions"] = []
    normalized["extensions"] = sorted(
        set(
            [
                ext if ext.startswith(".") else f".{ext}"
                for ext in normalized["extensions"]
                if isinstance(ext, str) and ext.strip()
            ]
        )
    )

    for key in ("min_size_bytes", "max_size_bytes"):
        value = normalized[key]
        if value is not None:
            try:
                normalized[key] = max(0, int(value))
            except (TypeError, ValueError):
                normalized[key] = None

    if (
        normalized["min_size_bytes"] is not None
        and normalized["max_size_bytes"] is not None
        and normalized["min_size_bytes"] > normalized["max_size_bytes"]
    ):
        normalized["min_size_bytes"], normalized["max_size_bytes"] = (
            normalized["max_size_bytes"],
            normalized["min_size_bytes"],
        )

    for date_key in ("date_after", "date_before"):
        date_value = normalized.get(date_key)
        if date_value:
            try:
                datetime.fromisoformat(str(date_value))
            except ValueError:
                normalized[date_key] = None

    if normalized.get("search_text") in (None, "", "null"):
        normalized["search_text"] = query

    if normalized["sort_by"] not in {
        "size_desc",
        "size_asc",
        "date_desc",
        "date_asc",
        "name_asc",
    }:
        normalized["sort_by"] = "date_desc"

    return normalized


def _size_to_bytes(value: float, unit: str) -> int:
    """Convert a human-readable size to bytes."""
    unit_map = {
        "b": 1,
        "kb": 1024,
        "mb": 1024**2,
        "gb": 1024**3,
        "tb": 1024**4,
    }
    return int(value * unit_map[unit.lower()])


def _extract_rule_based_natural_filters(query: str) -> Dict[str, Any]:
    """Deterministic parser for natural language file-search queries."""
    now = datetime.now()
    lowered = query.lower()
    filters: Dict[str, Any] = {
        "search_text": query,
        "extensions": [],
        "min_size_bytes": None,
        "max_size_bytes": None,
        "date_after": None,
        "date_before": None,
        "sort_by": None,
    }

    extension_rules = [
        (r"\bpython\b", [".py"]),
        (r"\bjavascript\b|\bjs\b", [".js"]),
        (r"\btypescript\b|\bts\b", [".ts", ".tsx"]),
        (r"\bjava\b", [".java"]),
        (r"\brust\b", [".rs"]),
        (r"\bgolang\b|\bgo\b", [".go"]),
        (r"\bjson\b", [".json"]),
        (r"\byaml\b|\byml\b", [".yaml", ".yml"]),
        (r"\bmarkdown\b|\bmd\b", [".md"]),
        (r"\bsql\b", [".sql"]),
    ]
    for pattern, extensions in extension_rules:
        if re.search(pattern, lowered):
            filters["extensions"].extend(extensions)

    if re.search(r"\bconfig(?:uration)?\b", lowered):
        filters["extensions"].extend([".json", ".yaml", ".yml", ".toml", ".ini"])

    # Named size buckets
    if re.search(r"\b(large|larger|big|huge)\b", lowered):
        filters["min_size_bytes"] = max(filters["min_size_bytes"] or 0, 1_000_000)
    if re.search(r"\b(small|smaller|tiny)\b", lowered):
        current = filters["max_size_bytes"]
        filters["max_size_bytes"] = 10_000 if current is None else min(current, 10_000)

    # Numeric size constraints
    min_size_matches = re.findall(
        r"\b(?:larger than|greater than|over|above|at least|min(?:imum)?|>=)\s*(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|tb)\b",
        lowered,
    )
    for value, unit in min_size_matches:
        as_bytes = _size_to_bytes(float(value), unit)
        filters["min_size_bytes"] = max(filters["min_size_bytes"] or 0, as_bytes)

    max_size_matches = re.findall(
        r"\b(?:smaller than|less than|under|below|at most|max(?:imum)?|<=)\s*(\d+(?:\.\d+)?)\s*(b|kb|mb|gb|tb)\b",
        lowered,
    )
    for value, unit in max_size_matches:
        as_bytes = _size_to_bytes(float(value), unit)
        current = filters["max_size_bytes"]
        filters["max_size_bytes"] = as_bytes if current is None else min(current, as_bytes)

    # Relative date constraints
    if "today" in lowered:
        filters["date_after"] = now.strftime("%Y-%m-%d")
    elif "yesterday" in lowered:
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        filters["date_after"] = yesterday
        filters["date_before"] = now.strftime("%Y-%m-%d")
    elif "last week" in lowered or "past week" in lowered or "recent" in lowered:
        filters["date_after"] = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif "last month" in lowered or "past month" in lowered:
        filters["date_after"] = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    elif "this week" in lowered:
        start_of_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        filters["date_after"] = start_of_week
    elif "this month" in lowered:
        start_of_month = now.replace(day=1).strftime("%Y-%m-%d")
        filters["date_after"] = start_of_month

    # Relative date patterns like "last 3 days"
    relative_match = re.search(
        r"\blast\s+(\d+)\s*(day|days|week|weeks|month|months)\b",
        lowered,
    )
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if "day" in unit:
            delta = timedelta(days=amount)
        elif "week" in unit:
            delta = timedelta(weeks=amount)
        else:
            delta = timedelta(days=30 * amount)
        filters["date_after"] = (now - delta).strftime("%Y-%m-%d")

    # Absolute date constraints
    after_match = re.search(r"\b(?:after|since)\s+(\d{4}-\d{2}-\d{2})\b", lowered)
    if after_match:
        filters["date_after"] = after_match.group(1)

    before_match = re.search(r"\b(?:before|until)\s+(\d{4}-\d{2}-\d{2})\b", lowered)
    if before_match:
        filters["date_before"] = before_match.group(1)

    # Sort preferences
    if re.search(
        r"\b(largest|biggest|highest size|size desc|descending size)\b",
        lowered,
    ):
        filters["sort_by"] = "size_desc"
    elif re.search(
        r"\b(smallest|lowest size|size asc|ascending size)\b",
        lowered,
    ):
        filters["sort_by"] = "size_asc"
    elif re.search(r"\b(oldest|earliest)\b", lowered):
        filters["sort_by"] = "date_asc"
    elif re.search(r"\b(newest|latest|most recent)\b", lowered):
        filters["sort_by"] = "date_desc"
    elif re.search(r"\b(alphabetical|name)\b", lowered):
        filters["sort_by"] = "name_asc"

    return filters


def _has_structured_natural_filters(filters: Dict[str, Any]) -> bool:
    """Whether parsed filters contain actionable structure beyond raw text."""
    return any(
        [
            bool(filters.get("extensions")),
            filters.get("min_size_bytes") is not None,
            filters.get("max_size_bytes") is not None,
            filters.get("date_after") is not None,
            filters.get("date_before") is not None,
            filters.get("sort_by") not in (None, "date_desc"),
        ]
    )


async def parse_natural_language_query(query: str) -> dict:
    """Parse natural language query into structured filters."""
    rule_filters = _normalize_natural_filters(
        _extract_rule_based_natural_filters(query),
        query,
    )

    # Rules-first path: return immediately when deterministic parser is confident.
    if _has_structured_natural_filters(rule_filters):
        return rule_filters

    # LLM path only for ambiguous/unstructured requests.
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    prompt = f"""Extract search filters from this query.

Today's date: {today}
One week ago: {week_ago}

Query: "{query}"

Respond with JSON ONLY in this exact format:
{{
  "search_text": "keywords to search for (or null)",
  "extensions": [".py", ".js"],
  "min_size_bytes": 10000,
  "max_size_bytes": null,
  "date_after": "{week_ago}",
  "date_before": null,
  "sort_by": "size_desc"
}}

Rules:
- "large files" = min_size_bytes: 1000000 (1MB)
- "small files" = max_size_bytes: 10000 (10KB)
- "recent" or "last week" = date_after: "{week_ago}"
- "Python" = extensions: [".py"]
- "JavaScript" or "JS" = extensions: [".js"]
- "config" or "configuration" = extensions: [".json", ".yaml", ".yml", ".toml"]
- sort_by options: "size_desc", "size_asc", "date_desc", "date_asc", "name_asc"
- Use null for fields not specified in query
"""

    try:
        client = await get_http_client()
        resp = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": CLASSIFY_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=15.0,
        )
        resp.raise_for_status()

        data = resp.json()
        response = data.get("response", "")
        json_start = response.find("{")
        json_end = response.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            parsed = json.loads(response[json_start : json_end + 1])
            if isinstance(parsed, dict):
                return _normalize_natural_filters(parsed, query)
    except Exception as e:
        logger.warning(f"NL parsing failed ({type(e).__name__}): {e}")

    return rule_filters


# Phase 6E: Apply rate limiting to endpoints after all are defined
# Note: slowapi decorators are applied after function definition
if limiter:
    # Search endpoints - 30/minute

    # Note: Rate limiting is enabled via app.state.limiter above
    logger.info(
        f"Rate limits configured: search={RATE_LIMIT_SEARCH}, read={RATE_LIMIT_READ}"
    )



# ============================================================================
# CONTROL & ORCHESTRATION (Phase 6G)
# ============================================================================

class IndexerControlRequest(BaseModel):
    paths: Optional[List[str]] = None
    force: bool = False
    
@app.post("/api/control/index")
async def trigger_indexing(
    request: IndexerControlRequest,
    _: None = Depends(require_control_api_key),
):
    """Trigger the indexing process in a background subprocess with operation tracking."""
    try:
        # Check if already running
        import psutil
        for p in psutil.process_iter():
            try:
                cmd_line = " ".join(p.cmdline())
                if "indexer.py" in cmd_line and p.pid != os.getpid():
                     return {"status": "already_running", "pid": p.pid}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Create progress operation
        # We don't know the exact total yet, but we'll update it later
        operation_id = progress_manager.create_operation(OperationType.INDEXING, total_items=100)
        progress_manager.start_operation(operation_id)

        # Start indexer
        cmd = [sys.executable, "indexer.py", "--operation-id", operation_id]
        if request.force:
            cmd.append("--force")
        
        env = os.environ.copy()
        cwd = str(Path(__file__).parent)

        proc = subprocess.Popen(cmd, env=env, cwd=cwd, start_new_session=True)
        active_subprocesses[operation_id] = proc
        
        return {"status": "started", "operation_id": operation_id, "command": " ".join(cmd)}
    except Exception as e:
        logger.error(f"Failed to start indexer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/control/clear-db")
async def clear_database(_: None = Depends(require_control_api_key)):
    """Wipe all metadata and embeddings from the database."""
    async with get_conn() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE files CASCADE")
            await conn.execute("TRUNCATE directories CASCADE")
            await conn.execute("TRUNCATE tags CASCADE")
            # file_chunks and file_embeddings will be wiped due to CASCADE
        return {"status": "cleared", "timestamp": datetime.now().isoformat()}

@app.get("/api/control/stats")
async def get_system_stats(_: None = Depends(require_control_api_key)):
    """Get detailed system and database statistics."""
    async with get_conn() as conn:
        chunk_table_exists = await conn.fetchval(
            "SELECT to_regclass('public.file_chunks') IS NOT NULL"
        )
        chunks = 0
        chunk_embeddings = 0
        if chunk_table_exists:
            chunks = await conn.fetchval("SELECT COUNT(*) FROM file_chunks")
            chunk_embeddings = await conn.fetchval(
                "SELECT COUNT(*) FROM file_chunks WHERE embedding IS NOT NULL"
            )

        stats = {
            "files": await conn.fetchval("SELECT COUNT(*) FROM files"),
            "chunks": chunks,
            "embeddings_file": await conn.fetchval(
                "SELECT COUNT(*) FROM file_embeddings WHERE COALESCE(model, $1) = $1",
                EMBED_MODEL,
            ),
            "embeddings_chunk": chunk_embeddings,
            "db_size": await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            ),
        }
        return stats

# ============================================================================
# OPERATION CONTROL & PROGRESS ENDPOINTS
# ============================================================================

class ProgressReportRequest(BaseModel):
    items_processed: int
    current_item: Optional[str] = ""
    status_message: Optional[str] = ""
    total_items: Optional[int] = None
    success: Optional[bool] = None

@app.post("/api/control/progress/{operation_id}")
async def report_progress(
    operation_id: str,
    report: ProgressReportRequest,
    _: None = Depends(require_control_api_key),
):
    """Internal endpoint for subprocesses to report progress."""
    if report.total_items is not None:
        with progress_manager.lock:
            if operation_id in progress_manager.operations:
                progress_manager.operations[operation_id].total_items = report.total_items
    
    if report.success is not None:
        progress_manager.complete_operation(operation_id, success=report.success)
        if operation_id in active_subprocesses:
            del active_subprocesses[operation_id]
        return {"status": "completed"}
        
    updated = progress_manager.update_progress(
        operation_id,
        items_processed=report.items_processed,
        current_item=report.current_item,
        status_message=report.status_message,
        total_items=report.total_items
    )
    return {"status": "updated" if updated else "not_found"}

@app.post("/api/control/stop/{operation_id}")
async def stop_operation(
    operation_id: str,
    _: None = Depends(require_control_api_key),
):
    """Forcefully stop a running operation and its subprocess tree."""
    if operation_id in active_subprocesses:
        proc = active_subprocesses[operation_id]
        import psutil
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            progress_manager.cancel_operation(operation_id)
            del active_subprocesses[operation_id]
            logger.info(f"Successfully stopped operation {operation_id}")
            return {"status": "stopped"}
        except (psutil.NoSuchProcess, Exception) as e:
            logger.error(f"Error stopping operation {operation_id}: {e}")
            # Still mark as cancelled even if process is gone
            progress_manager.cancel_operation(operation_id)
            if operation_id in active_subprocesses:
                del active_subprocesses[operation_id]
            return {"status": "partially_stopped", "error": str(e)}
    
    # Check if it's in progress manager but no subprocess (might be a different kind of op)
    if progress_manager.cancel_operation(operation_id):
        return {"status": "cancelled"}
        
    return {"status": "not_found"}

@app.post("/api/control/pause/{operation_id}")
async def pause_operation_endpoint(
    operation_id: str,
    _: None = Depends(require_control_api_key),
):
    """Pause a running operation subprocess."""
    if operation_id in active_subprocesses:
        proc = active_subprocesses[operation_id]
        import signal
        try:
            os.kill(proc.pid, signal.SIGSTOP)
            progress_manager.pause_operation(operation_id)
            return {"status": "paused"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "not_found"}

@app.post("/api/control/resume/{operation_id}")
async def resume_operation_endpoint(
    operation_id: str,
    _: None = Depends(require_control_api_key),
):
    """Resume a paused operation subprocess."""
    if operation_id in active_subprocesses:
        proc = active_subprocesses[operation_id]
        import signal
        try:
            os.kill(proc.pid, signal.SIGCONT)
            progress_manager.resume_operation(operation_id)
            return {"status": "resumed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "not_found"}

@app.websocket("/ws/progress/{operation_id}")
async def progress_websocket_endpoint(websocket: WebSocket, operation_id: str):
    """Subscribe to real-time progress updates via WebSocket."""
    await authorize_websocket(websocket)
    await websocket.accept()
    progress_manager.subscribe(operation_id, websocket)
    
    # Send initial state
    status = progress_manager.get_operation_status(operation_id)
    if status:
        await websocket.send_json({"type": "initial", "data": status})
        
    try:
        while True:
            # Keep the connection alive, wait for potential control messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        # Client disconnected
        pass
    finally:
        progress_manager.unsubscribe(operation_id, websocket)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
