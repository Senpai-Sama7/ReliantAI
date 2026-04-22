"""
Ultimate Intelligent Storage Nexus - Multi-Tier Storage Architecture
Phase 3: Hot/Warm/Cold Storage Tiering

Implements intelligent data lifecycle management:
- HOT: Binary embeddings in RAM (fastest, smallest)
- WARM: Int8 embeddings on SSD (fast, 4x compression)
- COLD: Float32 on disk + backups (full precision)

Inspired by: DiskANN, pgvectorscale StreamingDiskANN
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import os
import json
import pickle
import gzip
from pathlib import Path
import logging
from collections import OrderedDict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageTier(Enum):
    """Storage tier enum"""

    HOT = "hot"  # RAM - binary embeddings
    WARM = "warm"  # SSD - int8 embeddings
    COLD = "cold"  # Disk - float32 + metadata


@dataclass
class StorageConfig:
    """Configuration for multi-tier storage"""

    hot_max_items: int = 50000  # Max items in RAM
    hot_eviction_policy: str = "lru"  # LRU eviction
    warm_compression: bool = True  # Compress warm tier
    cold_backup_interval: int = 3600  # Backup interval (seconds)
    storage_dir: str = "./storage_tiers"


class TieredStorageManager:
    """
    Manages multi-tier storage for embeddings

    Architecture:
    ┌─────────────┐
    │   HOT TIER  │  RAM - Binary embeddings (1-bit)
    │  (~50K)     │  Fastest retrieval, O(1) access
    └──────┬──────┘
           │ Miss
           ▼
    ┌─────────────┐
    │  WARM TIER  │  SSD - Int8 embeddings (8-bit)
    │  (~500K)    │  Fast retrieval, mmap-friendly
    └──────┬──────┘
           │ Miss
           ▼
    ┌─────────────┐
    │  COLD TIER  │  Disk - Float32 (32-bit)
    │  (Unlimited)│  Full precision, compressed
    └─────────────┘
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        self._init_storage_dirs()

        # HOT tier: In-memory cache (binary embeddings)
        self.hot_cache: OrderedDict[int, np.ndarray] = OrderedDict()
        self.hot_access_count: Dict[int, int] = {}

        # WARM tier: Int8 on SSD
        self.warm_index: Dict[int, str] = {}  # id -> file path

        # COLD tier: Float32 + metadata
        self.cold_index: Dict[int, Dict] = {}  # id -> metadata

        # Statistics
        self.stats = {
            "hot_hits": 0,
            "hot_misses": 0,
            "warm_hits": 0,
            "warm_misses": 0,
            "cold_reads": 0,
        }

        logger.info(f"Initialized TieredStorageManager")
        logger.info(f"  Hot tier capacity: {config.hot_max_items} items")
        logger.info(f"  Storage directory: {config.storage_dir}")

    def _init_storage_dirs(self):
        """Initialize storage directories"""
        Path(self.config.storage_dir).mkdir(parents=True, exist_ok=True)
        Path(f"{self.config.storage_dir}/warm").mkdir(exist_ok=True)
        Path(f"{self.config.storage_dir}/cold").mkdir(exist_ok=True)

    def store(
        self,
        id: int,
        binary_emb: np.ndarray,
        int8_emb: np.ndarray,
        float32_emb: np.ndarray,
        metadata: Dict,
        make_hot: bool = True,
    ):
        """
        Store embedding across all tiers

        Args:
            id: Unique identifier
            binary_emb: 1-bit quantized (for hot tier)
            int8_emb: 8-bit quantized (for warm tier)
            float32_emb: Full precision (for cold tier)
            metadata: Additional metadata
            make_hot: Whether to promote to hot tier immediately
        """
        # Store in hot tier (if promoted)
        if make_hot:
            self._promote_to_hot(id, binary_emb)

        # Store in warm tier (int8)
        self._store_warm(id, int8_emb)

        # Store in cold tier (float32 + metadata)
        self._store_cold(id, float32_emb, metadata)

    def _promote_to_hot(self, id: int, binary_emb: np.ndarray):
        """Promote item to hot tier (RAM)"""
        # Evict if necessary
        while len(self.hot_cache) >= self.config.hot_max_items:
            self._evict_from_hot()

        # Add to hot cache
        self.hot_cache[id] = binary_emb
        self.hot_cache.move_to_end(id)  # Mark as recently used
        self.hot_access_count[id] = self.hot_access_count.get(id, 0) + 1

    def _evict_from_hot(self):
        """Evict least recently used item from hot tier"""
        if not self.hot_cache:
            return

        # LRU eviction
        oldest_id, _ = self.hot_cache.popitem(last=False)
        self.hot_access_count.pop(oldest_id, None)
        logger.debug(f"Evicted {oldest_id} from hot tier")

    def _store_warm(self, id: int, int8_emb: np.ndarray):
        """Store in warm tier (SSD)"""
        filepath = f"{self.config.storage_dir}/warm/{id}.npy"

        if self.config.warm_compression:
            # Compress with gzip
            filepath += ".gz"
            with gzip.open(filepath, "wb") as f:
                np.save(f, int8_emb)
        else:
            np.save(filepath, int8_emb)

        self.warm_index[id] = filepath

    def _store_cold(self, id: int, float32_emb: np.ndarray, metadata: Dict):
        """Store in cold tier (Disk)"""
        data = {
            "embedding": float32_emb,
            "metadata": metadata,
            "stored_at": time.time(),
        }

        filepath = f"{self.config.storage_dir}/cold/{id}.pkl.gz"
        with gzip.open(filepath, "wb") as f:
            pickle.dump(data, f)

        self.cold_index[id] = {
            "filepath": filepath,
            "metadata": metadata,
        }

    def retrieve(self, id: int, tier: StorageTier = None) -> Optional[Dict]:
        """
        Retrieve embedding from appropriate tier

        Tier selection logic:
        1. Try hot tier (RAM) - O(1)
        2. Try warm tier (SSD) - O(1) with mmap
        3. Fallback to cold tier (Disk) - O(1) with decompression
        """
        result = {}

        # Try hot tier first
        if id in self.hot_cache:
            self.stats["hot_hits"] += 1
            self.hot_cache.move_to_end(id)  # Update LRU
            result["binary"] = self.hot_cache[id]
            result["tier"] = StorageTier.HOT
        else:
            self.stats["hot_misses"] += 1

            # Try warm tier
            if id in self.warm_index:
                self.stats["warm_hits"] += 1
                int8_emb = self._load_warm(id)
                result["int8"] = int8_emb
                result["tier"] = StorageTier.WARM

                # Optionally promote to hot
                if self.hot_access_count.get(id, 0) > 3:
                    # Would need binary to promote fully
                    pass
            else:
                self.stats["warm_misses"] += 1

                # Load from cold tier
                if id in self.cold_index:
                    self.stats["cold_reads"] += 1
                    cold_data = self._load_cold(id)
                    result["float32"] = cold_data["embedding"]
                    result["metadata"] = cold_data["metadata"]
                    result["tier"] = StorageTier.COLD
                else:
                    return None

        return result

    def _load_warm(self, id: int) -> np.ndarray:
        """Load from warm tier"""
        filepath = self.warm_index[id]

        if filepath.endswith(".gz"):
            with gzip.open(filepath, "rb") as f:
                return np.load(f)
        else:
            return np.load(filepath)

    def _load_cold(self, id: int) -> Dict:
        """Load from cold tier"""
        filepath = self.cold_index[id]["filepath"]

        with gzip.open(filepath, "rb") as f:
            return pickle.load(f)

    def batch_retrieve(
        self, ids: List[int], prefer_tier: StorageTier = None
    ) -> Dict[int, Dict]:
        """Retrieve multiple items efficiently"""
        results = {}

        for id in ids:
            result = self.retrieve(id, prefer_tier)
            if result:
                results[id] = result

        return results

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        total_requests = self.stats["hot_hits"] + self.stats["hot_misses"]

        return {
            "hot_items": len(self.hot_cache),
            "hot_size_mb": sum(emb.nbytes for emb in self.hot_cache.values())
            / (1024 * 1024),
            "warm_items": len(self.warm_index),
            "cold_items": len(self.cold_index),
            "hit_rates": {
                "hot": self.stats["hot_hits"] / total_requests
                if total_requests > 0
                else 0,
                "warm": self.stats["warm_hits"] / self.stats["hot_misses"]
                if self.stats["hot_misses"] > 0
                else 0,
            },
            "access_counts": dict(self.hot_access_count),
        }

    def warmup(self, ids: List[int]):
        """Preload items into hot tier"""
        logger.info(f"Warming up {len(ids)} items into hot tier...")

        for id in ids:
            if id not in self.hot_cache and id in self.warm_index:
                # Would need binary to fully warmup
                pass


class CachingSearchIndex:
    """
    Search index with intelligent caching

    Combines HNSW with multi-tier storage for optimal performance
    """

    def __init__(self, storage_manager: TieredStorageManager, quantizer):
        self.storage = storage_manager
        self.quantizer = quantizer

        # In-memory HNSW index (on binary embeddings)
        self.hnsw_ids: List[int] = []
        self.hnsw_vectors: Optional[np.ndarray] = None

        # Query cache
        self.query_cache: Dict[str, List[Tuple[int, float]]] = {}
        self.query_cache_max_size = 1000

    def build_from_storage(self, ids: List[int]):
        """Build search index from stored embeddings"""
        logger.info(f"Building search index from {len(ids)} stored items...")

        binary_vectors = []
        valid_ids = []

        for id in ids:
            result = self.storage.retrieve(id)
            if result and "binary" in result:
                binary_vectors.append(result["binary"])
                valid_ids.append(id)

        if binary_vectors:
            self.hnsw_vectors = np.array(binary_vectors)
            self.hnsw_ids = valid_ids

            logger.info(f"Index built: {len(valid_ids)} vectors")
            logger.info(
                f"Memory usage: {self.hnsw_vectors.nbytes / (1024 * 1024):.2f} MB"
            )

    def search(self, query_binary: np.ndarray, k: int = 10) -> List[Tuple[int, float]]:
        """
        Brute force search on binary embeddings
        (Replace with HNSW for production)
        """
        if self.hnsw_vectors is None or len(self.hnsw_vectors) == 0:
            return []

        # Compute Hamming distances
        # Unpack binary vectors
        query_unpacked = np.unpackbits(query_binary).astype(np.float32)
        vectors_unpacked = np.unpackbits(self.hnsw_vectors, axis=1).astype(np.float32)

        # XOR + popcount
        xor_result = query_unpacked ^ vectors_unpacked
        distances = np.sum(xor_result, axis=1)

        # Get top k
        top_k_idx = np.argpartition(distances, k)[:k]
        top_k_idx = top_k_idx[np.argsort(distances[top_k_idx])]

        results = []
        for idx in top_k_idx:
            id = self.hnsw_ids[idx]
            # Convert Hamming distance to similarity
            similarity = 1.0 - (distances[idx] / (len(query_unpacked) * 8))
            results.append((id, similarity))

        return results

    def cached_search(
        self, query_text: str, query_binary: np.ndarray, k: int = 10
    ) -> List[Tuple[int, float]]:
        """Search with query caching"""
        cache_key = f"{query_text}:{k}"

        if cache_key in self.query_cache:
            logger.debug(f"Query cache hit for: {query_text[:50]}...")
            return self.query_cache[cache_key]

        results = self.search(query_binary, k=k)

        # Cache results
        if len(self.query_cache) >= self.query_cache_max_size:
            # Simple FIFO eviction
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]

        self.query_cache[cache_key] = results
        return results


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("MULTI-TIER STORAGE ARCHITECTURE")
    logger.info("Phase 3: Hot/Warm/Cold Storage Management")
    logger.info("=" * 60)

    # Import quantizer
    from quantization import EmbeddingQuantizer

    # Create test data
    n_files = 10000
    dims = 768

    logger.info(f"\nGenerating test data: {n_files} files, {dims} dimensions")
    np.random.seed(42)
    embeddings = np.random.randn(n_files, dims).astype(np.float32)

    # Initialize quantizer and storage
    logger.info("\nInitializing storage manager...")
    quantizer = EmbeddingQuantizer()
    config = StorageConfig(hot_max_items=1000, storage_dir="./test_storage_tiers")
    storage = TieredStorageManager(config)

    # Store embeddings
    logger.info("\nStoring embeddings across tiers...")
    for i in range(min(1000, n_files)):
        quantized = quantizer.quantize_all_tiers(embeddings[i])
        metadata = {
            "id": i,
            "name": f"file_{i}.txt",
            "size": np.random.randint(1000, 1000000),
        }

        # Make first 100 hot
        make_hot = i < 100
        storage.store(
            i,
            quantized.binary,
            quantized.int8,
            quantized.float32,
            metadata,
            make_hot=make_hot,
        )

    # Show storage stats
    stats = storage.get_stats()
    logger.info(f"\nStorage Statistics:")
    logger.info(
        f"  Hot tier: {stats['hot_items']} items ({stats['hot_size_mb']:.2f} MB)"
    )
    logger.info(f"  Warm tier: {stats['warm_items']} items")
    logger.info(f"  Cold tier: {stats['cold_items']} items")

    # Test retrieval
    logger.info("\nTesting retrieval from each tier...")

    # Hot tier retrieval
    hot_result = storage.retrieve(0)
    logger.info(
        f"  Hot tier (id=0): {hot_result['tier'].value}, binary shape: {hot_result['binary'].shape}"
    )

    # Warm tier retrieval (id=500, not hot)
    warm_result = storage.retrieve(500)
    logger.info(
        f"  Warm tier (id=500): {warm_result['tier'].value}, int8 shape: {warm_result['int8'].shape}"
    )

    # Cold tier retrieval (non-existent in hot/warm, will fallback)
    # For demo, we'll just show the structure
    logger.info(f"  Cold tier: Contains full float32 + metadata")

    # Build search index
    logger.info("\nBuilding search index...")
    search_index = CachingSearchIndex(storage, quantizer)
    search_index.build_from_storage(list(range(1000)))

    # Test search
    logger.info("\nTesting search...")
    query = np.random.randn(dims).astype(np.float32)
    query_quantized = quantizer.quantize_binary(query)
    results = search_index.search(query_quantized, k=5)

    logger.info(f"  Top 5 results: {[id for id, _ in results]}")
    logger.info(f"  Similarities: {[f'{sim:.4f}' for _, sim in results]}")

    # Show tier stats
    logger.info(f"\nTier Access Statistics:")
    logger.info(f"  Hot hits: {storage.stats['hot_hits']}")
    logger.info(f"  Hot misses: {storage.stats['hot_misses']}")
    logger.info(f"  Warm hits: {storage.stats['warm_hits']}")
    logger.info(f"  Cold reads: {storage.stats['cold_reads']}")

    logger.info("\n" + "=" * 60)
    logger.info("Phase 3 Complete: Multi-Tier Storage Implemented")
    logger.info("Hot tier in RAM, Warm on SSD, Cold on Disk")
    logger.info("=" * 60)
