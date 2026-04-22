#!/usr/bin/env python3
"""
NEXUS Runtime Hostile Audit Test Suite

Comprehensive verification of:
- Memory region isolation (no overlaps)
- Atomic operation correctness
- Seqlock protocol safety
- Concurrent access safety

This is a REAL test suite - not mocked.
"""

import pytest
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/nexus-runtime')

from memory import (
    NexusMemoryManager,
    MemoryLayout,
    MemoryRegion,
    SharedMemoryBuffer,
    AtomicOrdering,
    RegionOverlapError,
    OutOfMemoryError,
)


class TestMemoryLayout:
    """Test memory layout management."""
    
    def test_region_creation(self):
        """Verify region creation with correct bounds."""
        region = MemoryRegion("test", 0x1000, 0x1000)
        assert region.offset == 0x1000
        assert region.size == 0x1000
        assert region.end == 0x2000
    
    def test_region_overlap_detection(self):
        """Verify overlap detection works correctly."""
        r1 = MemoryRegion("a", 0x1000, 0x1000)
        r2 = MemoryRegion("b", 0x1800, 0x1000)  # Overlaps with a
        r3 = MemoryRegion("c", 0x2000, 0x1000)  # Adjacent but not overlapping
        r4 = MemoryRegion("d", 0x3000, 0x1000)  # Far away
        
        assert r1.overlaps(r2), "Should detect overlap"
        assert r2.overlaps(r1), "Overlap is symmetric"
        assert not r1.overlaps(r3), "Adjacent is not overlapping"
        assert not r1.overlaps(r4), "Far regions don't overlap"
    
    def test_layout_allocation(self):
        """Verify layout can allocate regions without overlap."""
        layout = MemoryLayout(1024 * 1024)
        
        r1 = layout.allocate("region_a", 4096)
        r2 = layout.allocate("region_b", 4096)
        r3 = layout.allocate("region_c", 4096)
        
        # Verify no overlaps
        assert not r1.overlaps(r2)
        assert not r2.overlaps(r3)
        assert not r1.overlaps(r3)
        
        # Verify regions are recorded
        assert layout.get_region("region_a") == r1
        assert layout.get_region("region_b") == r2
        assert layout.get_region("region_c") == r3
    
    def test_layout_overlap_prevention(self):
        """Verify layout prevents overlapping allocations."""
        layout = MemoryLayout(1024 * 1024)
        
        # Allocate first region at fixed offset
        r1 = layout.allocate("region_a", 8192, offset=0x1000)
        
        # Attempting to allocate overlapping region should fail
        with pytest.raises(RegionOverlapError):
            layout.allocate("region_b", 4096, offset=0x1800)  # Overlaps with a
    
    def test_layout_out_of_memory(self):
        """Verify layout handles exhaustion."""
        layout = MemoryLayout(16384)  # Small layout
        
        layout.allocate("a", 4096)
        layout.allocate("b", 4096)
        layout.allocate("c", 4096)
        
        # This should fail - not enough space
        with pytest.raises(OutOfMemoryError):
            layout.allocate("d", 8192)
    
    def test_invariant_checker(self):
        """Verify invariant checker detects violations."""
        # This is a white-box test - we manually create overlapping regions
        # by bypassing the allocation check
        layout = MemoryLayout(1024 * 1024)
        
        # Manually inject overlapping regions (simulating corruption)
        layout._regions["a"] = MemoryRegion("a", 0x1000, 0x2000)
        layout._regions["b"] = MemoryRegion("b", 0x2000, 0x2000)  # Adjacent - OK
        layout._regions["c"] = MemoryRegion("c", 0x2800, 0x1000)  # Overlaps with b!
        
        violations = layout.check_invariants()
        assert violations != 0, "Should detect overlap between b and c"


class TestSharedMemoryBuffer:
    """Test shared memory buffer operations."""
    
    def test_basic_read_write(self):
        """Verify basic read/write operations."""
        buf = SharedMemoryBuffer(4096)
        
        # Write data
        test_data = b"Hello, NEXUS!"
        buf.write(0, test_data)
        
        # Read back
        result = buf.read(0, len(test_data))
        assert result == test_data
        
        buf.close()
    
    def test_zero_copy_view(self):
        """Verify memoryview provides zero-copy access."""
        buf = SharedMemoryBuffer(4096)
        
        # Write data
        test_data = b"ABCDEFGHIJ"
        buf.write(100, test_data)
        
        # Get zero-copy view
        view = buf.get_view(100, len(test_data))
        
        # View should reflect buffer contents without copy
        assert bytes(view) == test_data
        
        # Release view before closing buffer
        view.release()
        
        buf.close()
    
    def test_bounds_checking(self):
        """Verify out-of-bounds access is prevented."""
        buf = SharedMemoryBuffer(4096)
        
        with pytest.raises(Exception):  # MemoryError or similar
            buf.write(4000, b"X" * 200)  # Exceeds buffer
        
        with pytest.raises(Exception):  # MemoryError or similar
            buf.read(4000, 200)  # Exceeds buffer
        
        buf.close()
    
    def test_atomic_operations(self):
        """Verify atomic 32-bit operations."""
        buf = SharedMemoryBuffer(4096)
        
        # Test aligned atomic store/load
        buf.atomic_store_i32(0, 42)
        result = buf.atomic_load_i32(0)
        assert result == 42
        
        # Test at different offsets
        buf.atomic_store_i32(1024, 12345)
        result = buf.atomic_load_i32(1024)
        assert result == 12345
        
        # Test negative values (signed)
        buf.atomic_store_i32(2048, -1000)
        result = buf.atomic_load_i32(2048)
        assert result == -1000
        
        buf.close()
    
    def test_unaligned_access_rejected(self):
        """Verify unaligned atomic access is rejected."""
        buf = SharedMemoryBuffer(4096)
        
        with pytest.raises(Exception):  # MemoryError or similar
            buf.atomic_store_i32(1, 42)  # Unaligned
        
        with pytest.raises(Exception):  # MemoryError or similar
            buf.atomic_load_i32(2)  # Unaligned
        
        buf.close()
    
    def test_atomic_add(self):
        """Verify atomic increment."""
        buf = SharedMemoryBuffer(4096)
        
        buf.atomic_store_i32(0, 100)
        
        old = buf.atomic_add_i32(0, 50)
        assert old == 100
        
        new = buf.atomic_load_i32(0)
        assert new == 150
        
        buf.close()


class TestNexusMemoryManager:
    """Test high-level NEXUS memory manager."""
    
    def test_initialization(self):
        """Verify manager initializes correctly."""
        manager = NexusMemoryManager(1024 * 1024)
        
        # Control block should be allocated
        ctrl = manager.layout.get_region("control_block")
        assert ctrl is not None
        assert ctrl.offset == 0
        
        # Control block should be initialized
        write_idx = manager.buffer.atomic_load_i32(manager._ctrl_offset(manager.CTRL_WRITE_IDX))
        ready_idx = manager.buffer.atomic_load_i32(manager._ctrl_offset(manager.CTRL_READY_IDX))
        consume_idx = manager.buffer.atomic_load_i32(manager._ctrl_offset(manager.CTRL_CONSUME_IDX))
        
        assert write_idx == 0
        assert ready_idx == 0
        assert consume_idx == 1  # Special initialization
        
        manager.close()
    
    def test_region_allocation(self):
        """Verify region allocation through manager."""
        manager = NexusMemoryManager(1024 * 1024)
        
        fb_a = manager.allocate_region("framebuffer_a", 64 * 1024)
        fb_b = manager.allocate_region("framebuffer_b", 64 * 1024)
        ring = manager.allocate_region("input_ring", 16 * 1024)
        
        # Verify no overlaps
        assert not fb_a.overlaps(fb_b)
        assert not fb_a.overlaps(ring)
        assert not fb_b.overlaps(ring)
        
        # Verify control block doesn't overlap
        assert not manager.ctrl_block.overlaps(fb_a)
        
        manager.close()
    
    def test_invariants_pass_clean(self):
        """Verify invariants pass for valid layout."""
        manager = NexusMemoryManager(1024 * 1024)
        
        manager.allocate_region("a", 64 * 1024)
        manager.allocate_region("b", 64 * 1024)
        manager.allocate_region("c", 64 * 1024)
        
        violations = manager.check_invariants()
        assert violations == 0, f"Expected 0 violations, got {violations}"
        
        manager.close()
    
    def test_seqlock_consistent_read(self):
        """Verify seqlock provides consistent reads."""
        manager = NexusMemoryManager(1024 * 1024)
        
        # Set up some control state
        manager.buffer.atomic_store_i32(
            manager._ctrl_offset(manager.CTRL_WRITE_IDX), 0
        )
        manager.buffer.atomic_store_i32(
            manager._ctrl_offset(manager.CTRL_READY_IDX), 1
        )
        
        def read_control():
            return {
                'write': manager.buffer.atomic_load_i32(
                    manager._ctrl_offset(manager.CTRL_WRITE_IDX)
                ),
                'ready': manager.buffer.atomic_load_i32(
                    manager._ctrl_offset(manager.CTRL_READY_IDX)
                ),
            }
        
        # Perform seqlock read
        result, retries, consistent = manager.seqlock_read(read_control)
        
        assert consistent, "Read should be consistent when no writer"
        assert result == {'write': 0, 'ready': 1}
        assert retries == 0  # Should succeed on first try
        
        manager.close()


class TestConcurrency:
    """Test concurrent access patterns."""
    
    def test_concurrent_atomic_increments(self):
        """Verify atomic increments are race-safe."""
        buf = SharedMemoryBuffer(4096)
        
        # Initialize counter
        buf.atomic_store_i32(0, 0)
        
        # Increment from multiple threads
        def incrementer():
            for _ in range(100):
                buf.atomic_add_i32(0, 1)
                time.sleep(0.0001)  # Small delay to increase contention
        
        # Run 10 threads, each incrementing 100 times
        threads = [threading.Thread(target=incrementer) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify final count
        final = buf.atomic_load_i32(0)
        assert final == 1000, f"Expected 1000, got {final}"
        
        buf.close()
    
    def test_seqlock_writer_reader_race(self):
        """Verify seqlock handles writer-reader races."""
        manager = NexusMemoryManager(1024 * 1024)
        
        # Set up test data regions
        data_region = manager.allocate_region("test_data", 4096)
        
        write_count = [0]
        read_count = [0]
        inconsistent_reads = [0]
        errors = []
        
        def writer():
            """Writer thread - continuously updates data with seqlock."""
            for i in range(100):
                def do_write():
                    # Write a pattern
                    manager.buffer.write(data_region.offset, struct.pack('<II', i, i * 2))
                    write_count[0] += 1
                
                manager.seqlock_write(do_write)
                time.sleep(0.001)
        
        def reader():
            """Reader thread - reads data with seqlock protection."""
            import struct
            for _ in range(200):
                def do_read():
                    data = manager.buffer.read(data_region.offset, 8)
                    val1, val2 = struct.unpack('<II', data)
                    return val1, val2
                
                result, retries, consistent = manager.seqlock_read(do_read)
                read_count[0] += 1
                
                if not consistent:
                    inconsistent_reads[0] += 1
                else:
                    # Verify data consistency (val2 should be val1 * 2)
                    val1, val2 = result
                    if val1 * 2 != val2:
                        errors.append(f"Data inconsistency: {val1}, {val2}")
        
        import struct  # Need for reader
        
        # Run writer and reader concurrently
        writer_thread = threading.Thread(target=writer)
        reader_thread = threading.Thread(target=reader)
        
        writer_thread.start()
        reader_thread.start()
        
        writer_thread.join()
        reader_thread.join()
        
        # Verify results
        assert write_count[0] == 100, f"Expected 100 writes, got {write_count[0]}"
        assert read_count[0] == 200, f"Expected 200 reads, got {read_count[0]}"
        assert len(errors) == 0, f"Data errors: {errors}"
        
        # Some inconsistent reads are expected due to race
        # But we should have gotten many consistent reads too
        assert inconsistent_reads[0] < 100, "Too many inconsistent reads"
        
        manager.close()


class TestMemoryMapOutput:
    """Test memory map visualization."""
    
    def test_memory_map_format(self):
        """Verify memory map is properly formatted."""
        manager = NexusMemoryManager(1024 * 1024)
        
        manager.allocate_region("framebuffer_a", 64 * 1024)
        manager.allocate_region("framebuffer_b", 64 * 1024)
        
        map_str = manager.get_memory_map()
        
        # Verify header
        assert "NEXUS Memory Map" in map_str
        assert "1.0 MB" in map_str
        
        # Verify regions are listed
        assert "framebuffer_a" in map_str
        assert "framebuffer_b" in map_str
        assert "control_block" in map_str
        
        # Verify format includes hex addresses
        assert "0x" in map_str
        
        manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
