#!/usr/bin/env python3
"""
NEXUS Runtime - Shared Memory & Synchronization Primitives

Python implementation of NEXUS architecture for ReliantAI:
- SharedArrayBuffer-equivalent via mmap
- Mesa-semantics atomic operations
- Seqlock synchronization protocol
- Memory layout management with overlap detection

Usage:
    from nexus_runtime import NexusMemoryManager
    
    manager = NexusMemoryManager(16 * 1024 * 1024)  # 16MB
    region = manager.allocate_region("data", 64 * 1024)
    
    # Use atomic operations
    manager.buffer.atomic_store_i32(offset, value)
    
    # Seqlock-protected read
    result, retries, consistent = manager.seqlock_read(read_fn)
"""

from .memory import (
    NexusMemoryManager,
    MemoryLayout,
    MemoryRegion,
    SharedMemoryBuffer,
    AtomicOrdering,
    MemoryError,
    RegionOverlapError,
    OutOfMemoryError,
)

from .data_layout import (
    Record,
    SoAFieldBatch,
    PhaseBoundaryTransformer,
    CacheSimulator,
    benchmark_layouts,
)

__version__ = "0.1.0"
__all__ = [
    # Memory management
    "NexusMemoryManager",
    "MemoryLayout",
    "MemoryRegion",
    "SharedMemoryBuffer",
    "AtomicOrdering",
    "MemoryError",
    "RegionOverlapError",
    "OutOfMemoryError",
    # Data layout
    "Record",
    "SoAFieldBatch",
    "PhaseBoundaryTransformer",
    "CacheSimulator",
    "benchmark_layouts",
]
