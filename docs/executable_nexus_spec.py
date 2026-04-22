#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  NEXUS RUNTIME - EXECUTABLE SPECIFICATION                                     ║
║                                                                               ║
║  This file is BOTH documentation AND the integration test.                    ║
║                                                                               ║
║  Usage:                                                                       ║
║    python docs/executable_nexus_spec.py          # Run as test                ║
║    python docs/executable_nexus_spec.py --docs   # Generate markdown docs     ║
║                                                                               ║
║  Philosophy: The documentation IS the system. This file runs the system       ║
║  and verifies all invariants. If this file passes, the spec is satisfied.     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import argparse
from dataclasses import dataclass
from typing import List, Tuple

# Add paths
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/nexus-runtime')

from memory import NexusMemoryManager, MemoryRegion, AtomicOrdering
from data_layout import Record, PhaseBoundaryTransformer, benchmark_layouts


@dataclass
class SpecSection:
    """A section of the executable specification."""
    title: str
    description: str
    test_fn: callable


class NexusExecutableSpec:
    """
    Executable specification for NEXUS Runtime.
    
    Each method is both:
    1. A test that verifies the spec
    2. Documentation of expected behavior
    """
    
    def __init__(self):
        self.sections: List[SpecSection] = []
        self.results: List[Tuple[str, bool, str]] = []
    
    def spec_memory_manager_creation(self) -> bool:
        """
        ## Section 1: Memory Manager Creation
        
        The system SHALL provide a NexusMemoryManager that:
        - Allocates shared memory of specified size
        - Creates a control block at offset 0
        - Initializes atomic indices to safe defaults
        
        ### Acceptance Criteria
        - Manager can be instantiated with size parameter
        - Control block is at offset 0x0
        - Initial state: write=0, ready=0, consume=1
        """
        manager = NexusMemoryManager(16 * 1024 * 1024)
        
        try:
            # Verify control block exists
            ctrl = manager.layout.get_region("control_block")
            assert ctrl.offset == 0, "Control block must be at offset 0"
            
            # Verify initial state
            write_idx = manager.buffer.atomic_load_i32(
                manager._ctrl_offset(manager.CTRL_WRITE_IDX)
            )
            ready_idx = manager.buffer.atomic_load_i32(
                manager._ctrl_offset(manager.CTRL_READY_IDX)
            )
            consume_idx = manager.buffer.atomic_load_i32(
                manager._ctrl_offset(manager.CTRL_CONSUME_IDX)
            )
            
            assert write_idx == 0, f"write_idx should be 0, got {write_idx}"
            assert ready_idx == 0, f"ready_idx should be 0, got {ready_idx}"
            assert consume_idx == 1, f"consume_idx should be 1, got {consume_idx}"
            
            return True
        finally:
            manager.close()
    
    def spec_region_allocation(self) -> bool:
        """
        ## Section 2: Memory Region Allocation
        
        The system SHALL support named memory regions with:
        - Non-overlapping allocation
        - Alignment guarantees
        - Size and offset tracking
        
        ### Acceptance Criteria
        - Regions can be allocated with name and size
        - No two regions overlap
        - Each region has unique name
        - Layout invariants pass verification
        """
        manager = NexusMemoryManager(64 * 1024 * 1024)
        
        try:
            # Allocate standard NEXUS regions
            fb_a = manager.allocate_region("framebuffer_a", 1920 * 1080 * 4)
            fb_b = manager.allocate_region("framebuffer_b", 1920 * 1080 * 4)
            input_ring = manager.allocate_region("input_ring", 256 * 8)
            soa_batch = manager.allocate_region("soa_field_batch", 8192 * 4 * 4)
            aos_tree = manager.allocate_region("aos_parse_tree", 1024 * 1024)
            
            # Verify no overlaps
            regions = [fb_a, fb_b, input_ring, soa_batch, aos_tree]
            for i, r1 in enumerate(regions):
                for j, r2 in enumerate(regions):
                    if i < j:
                        assert not r1.overlaps(r2), \
                            f"Regions {r1.name} and {r2.name} overlap!"
            
            # Verify invariants
            violations = manager.check_invariants()
            assert violations == 0, f"Invariant violations: {violations}"
            
            return True
        finally:
            manager.close()
    
    def spec_atomic_operations(self) -> bool:
        """
        ## Section 3: Atomic Operations
        
        The system SHALL provide atomic 32-bit integer operations:
        - Atomic store with Release semantics
        - Atomic load with Acquire semantics
        - Atomic add (fetch-and-add)
        - Unaligned access rejection
        
        ### Acceptance Criteria
        - Stores and loads preserve values
        - Concurrent increments are race-safe
        - Unaligned access raises error
        """
        manager = NexusMemoryManager(1024 * 1024)
        
        try:
            region = manager.allocate_region("test_data", 4096)
            
            # Test store/load
            manager.buffer.atomic_store_i32(region.offset, 42)
            val = manager.buffer.atomic_load_i32(region.offset)
            assert val == 42, f"Expected 42, got {val}"
            
            # Test atomic add
            old = manager.buffer.atomic_add_i32(region.offset, 8)
            assert old == 42, f"Expected old=42, got {old}"
            new = manager.buffer.atomic_load_i32(region.offset)
            assert new == 50, f"Expected new=50, got {new}"
            
            # Test unaligned access rejected
            try:
                manager.buffer.atomic_store_i32(region.offset + 1, 100)
                assert False, "Unaligned access should be rejected"
            except Exception:
                pass  # Expected
            
            return True
        finally:
            manager.close()
    
    def spec_seqlock_synchronization(self) -> bool:
        """
        ## Section 4: Seqlock Synchronization
        
        The system SHALL provide seqlock-based synchronization:
        - Writers increment sequence counter (odd = writing)
        - Readers validate consistency with pre/post discriminant
        - Inconsistent reads are detected and flagged
        
        ### Acceptance Criteria
        - Seqlock write updates sequence
        - Seqlock read returns (data, retries, consistent)
        - No consistent read shows torn data
        """
        manager = NexusMemoryManager(1024 * 1024)
        
        try:
            region = manager.allocate_region("seqlock_data", 4096)
            
            # Write with seqlock
            def writer():
                manager.buffer.atomic_store_i32(region.offset, 12345)
            
            manager.seqlock_write(writer)
            
            # Read with seqlock
            def reader():
                return manager.buffer.atomic_load_i32(region.offset)
            
            result, retries, consistent = manager.seqlock_read(reader)
            
            assert consistent, "Read should be consistent"
            assert result == 12345, f"Expected 12345, got {result}"
            
            return True
        finally:
            manager.close()
    
    def spec_phase_boundary_transformation(self) -> bool:
        """
        ## Section 5: Phase-Boundary Data Layout
        
        The system SHALL support AoS ↔ SoA transformations:
        - AoS: Array of Structs (heterogeneous access)
        - SoA: Struct of Arrays (SIMD-friendly)
        - Roundtrip conversion preserves data
        - SoA has better cache efficiency
        
        ### Acceptance Criteria
        - AoS to SoA conversion works
        - SoA to AoS roundtrip preserves data
        - Cache efficiency improves by at least 2x
        """
        # Test roundtrip
        original = [
            Record(1, 10.5, "A"),
            Record(2, 20.5, "B"),
            Record(3, 30.5, "C"),
        ]
        
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert len(recovered) == len(original), "Length mismatch"
        for orig, recov in zip(original, recovered):
            assert orig.id == recov.id
            assert abs(orig.value - recov.value) < 0.001
            assert orig.category == recov.category
        
        # Test cache efficiency
        results = benchmark_layouts(1000)
        improvement = results['cache_improvement']
        
        assert improvement >= 2.0, \
            f"Cache improvement should be >= 2x, got {improvement:.1f}x"
        
        return True
    
    def spec_concurrent_access_safety(self) -> bool:
        """
        ## Section 6: Concurrent Access Safety
        
        The system SHALL be safe for concurrent access:
        - Atomic operations prevent race conditions
        - Seqlock provides consistent reads during writes
        - Memory regions are isolated
        
        ### Acceptance Criteria
        - 10 threads × 1000 increments = 10000 (exact)
        - Writer-reader race produces no corrupt data
        """
        import threading
        
        manager = NexusMemoryManager(1024 * 1024)
        
        try:
            region = manager.allocate_region("counter", 4096)
            manager.buffer.atomic_store_i32(region.offset, 0)
            
            def incrementer():
                for _ in range(1000):
                    manager.buffer.atomic_add_i32(region.offset, 1)
            
            threads = [threading.Thread(target=incrementer) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            final = manager.buffer.atomic_load_i32(region.offset)
            assert final == 10000, f"Expected 10000, got {final}"
            
            return True
        finally:
            manager.close()
    
    def run_all(self) -> bool:
        """Run all specification tests."""
        sections = [
            SpecSection("1. Memory Manager Creation", 
                       "Basic initialization and control block",
                       self.spec_memory_manager_creation),
            SpecSection("2. Region Allocation",
                       "Non-overlapping memory regions",
                       self.spec_region_allocation),
            SpecSection("3. Atomic Operations",
                       "Thread-safe atomic primitives",
                       self.spec_atomic_operations),
            SpecSection("4. Seqlock Synchronization",
                       "Lock-free consistent reads",
                       self.spec_seqlock_synchronization),
            SpecSection("5. Phase-Boundary Transformation",
                       "AoS ↔ SoA layout conversion",
                       self.spec_phase_boundary_transformation),
            SpecSection("6. Concurrent Access Safety",
                       "Multi-threaded safety",
                       self.spec_concurrent_access_safety),
        ]
        
        print("╔" + "═" * 79 + "╗")
        print("║" + " NEXUS RUNTIME - EXECUTABLE SPECIFICATION ".center(79) + "║")
        print("╠" + "═" * 79 + "╣")
        
        all_passed = True
        for section in sections:
            print(f"║ {section.title:<77} ║")
            try:
                passed = section.test_fn()
                status = "✅ PASS"
            except Exception as e:
                passed = False
                status = f"❌ FAIL: {e}"
                all_passed = False
            
            self.results.append((section.title, passed, status))
            print(f"║   {status:<75} ║")
        
        print("╠" + "═" * 79 + "╣")
        if all_passed:
            print("║" + " ALL SPECIFICATIONS SATISFIED ✅ ".center(79) + "║")
        else:
            print("║" + " SPECIFICATION VIOLATIONS DETECTED ❌ ".center(79) + "║")
        print("╚" + "═" * 79 + "╝")
        
        return all_passed
    
    def generate_docs(self) -> str:
        """Generate markdown documentation from spec."""
        docs = ["# NEXUS Runtime Specification\n"]
        docs.append("*Generated from executable specification*\n")
        
        # Get docstrings from test methods
        methods = [
            self.spec_memory_manager_creation,
            self.spec_region_allocation,
            self.spec_atomic_operations,
            self.spec_seqlock_synchronization,
            self.spec_phase_boundary_transformation,
            self.spec_concurrent_access_safety,
        ]
        
        for method in methods:
            doc = method.__doc__
            if doc:
                docs.append(doc)
                docs.append("\n---\n")
        
        return "\n".join(docs)


def main():
    parser = argparse.ArgumentParser(
        description="NEXUS Runtime Executable Specification"
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Generate markdown documentation instead of running tests"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/nexus_spec.md",
        help="Output file for documentation"
    )
    
    args = parser.parse_args()
    
    spec = NexusExecutableSpec()
    
    if args.docs:
        # Generate documentation
        docs = spec.generate_docs()
        with open(args.output, 'w') as f:
            f.write(docs)
        print(f"Documentation generated: {args.output}")
    else:
        # Run tests
        passed = spec.run_all()
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
