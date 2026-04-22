#!/usr/bin/env python3
"""
Hostile Audit Tests for Phase-Boundary Data Layout

Verifies:
- AoS ↔ SoA roundtrip preserves data exactly
- Cache efficiency improvement is measurable
- In-place transforms work correctly
- No data corruption during conversion
"""

import pytest
import sys
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/nexus-runtime')

from data_layout import (
    Record,
    SoAFieldBatch,
    PhaseBoundaryTransformer,
    CacheSimulator,
    simulate_aos_access,
    simulate_soa_access,
    benchmark_layouts,
)


class TestRoundtripConversion:
    """Verify data integrity through AoS ↔ SoA conversions."""
    
    def test_empty_roundtrip(self):
        """Empty lists roundtrip correctly."""
        original = []
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        assert recovered == []
    
    def test_single_record_roundtrip(self):
        """Single record roundtrips correctly."""
        original = [Record(1, 10.5, "A")]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert len(recovered) == 1
        assert recovered[0].id == 1
        assert recovered[0].value == 10.5
        assert recovered[0].category == "A"
    
    def test_multiple_records_roundtrip(self):
        """Multiple records roundtrip correctly."""
        original = [
            Record(1, 10.5, "A"),
            Record(2, 20.5, "B"),
            Record(3, 30.5, "C"),
        ]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert len(recovered) == len(original)
        for i, (orig, recov) in enumerate(zip(original, recovered)):
            assert orig.id == recov.id, f"Record {i}: ID mismatch"
            assert abs(orig.value - recov.value) < 0.001, f"Record {i}: Value mismatch"
            assert orig.category == recov.category, f"Record {i}: Category mismatch"
    
    def test_large_dataset_roundtrip(self):
        """Large dataset roundtrips correctly."""
        original = [
            Record(i, float(i) * 1.5, f"cat_{i % 10}")
            for i in range(10000)
        ]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert len(recovered) == 10000
        # Spot check
        assert recovered[0].id == 0
        assert recovered[5000].id == 5000
        assert recovered[9999].id == 9999


class TestSoAOperations:
    """Test SoA-specific operations."""
    
    def test_soa_append(self):
        """Append adds records correctly."""
        batch = SoAFieldBatch()
        batch.append(1, 10.5, "A")
        batch.append(2, 20.5, "B")
        
        assert len(batch) == 2
        assert batch.ids[0] == 1
        assert batch.values[1] == 20.5
        assert batch.categories[0] == "A"
    
    def test_soa_get_record(self):
        """Get record reconstructs AoS correctly."""
        batch = SoAFieldBatch()
        batch.append(1, 10.5, "A")
        batch.append(2, 20.5, "B")
        
        r0 = batch.get_record(0)
        assert r0.id == 1
        assert r0.value == 10.5
        assert r0.category == "A"
        
        r1 = batch.get_record(1)
        assert r1.id == 2
    
    def test_soa_get_record_bounds(self):
        """Get record enforces bounds."""
        batch = SoAFieldBatch()
        batch.append(1, 10.5, "A")
        
        with pytest.raises(IndexError):
            batch.get_record(-1)
        
        with pytest.raises(IndexError):
            batch.get_record(1)  # Out of bounds
    
    def test_soa_slice_fields(self):
        """Slice fields returns correct subsets."""
        batch = SoAFieldBatch()
        for i in range(10):
            batch.append(i, float(i), f"cat_{i}")
        
        slice_data = batch.slice_fields(3, 7)
        
        assert list(slice_data['ids']) == [3, 4, 5, 6]
        assert list(slice_data['values']) == [3.0, 4.0, 5.0, 6.0]
        assert slice_data['categories'] == ['cat_3', 'cat_4', 'cat_5', 'cat_6']
    
    def test_in_place_transform(self):
        """In-place transform modifies values correctly."""
        batch = SoAFieldBatch()
        batch.append(1, 10.0, "A")
        batch.append(2, 20.0, "B")
        batch.append(3, 30.0, "C")
        
        PhaseBoundaryTransformer.transform_in_place(
            batch,
            lambda id, val: val * 2
        )
        
        assert batch.values[0] == 20.0
        assert batch.values[1] == 40.0
        assert batch.values[2] == 60.0
        # IDs unchanged
        assert batch.ids[0] == 1


class TestCacheSimulator:
    """Test cache simulation."""
    
    def test_cache_miss_detection(self):
        """Cache tracks misses correctly."""
        cache = CacheSimulator()
        
        # First access to a line - miss
        hit = cache.access(0x1000)
        assert not hit
        assert cache.miss_count == 1
        
        # Second access to same line - hit
        hit = cache.access(0x1008)  # Same cache line
        assert hit
        assert cache.hit_count == 1
        
        # Access to different line - miss
        hit = cache.access(0x2000)
        assert not hit
        assert cache.miss_count == 2
    
    def test_cache_miss_rate(self):
        """Miss rate calculation is correct."""
        cache = CacheSimulator()
        
        cache.access(0x1000)  # miss
        cache.access(0x1008)  # hit
        cache.access(0x1010)  # hit
        
        assert abs(cache.miss_rate - 1/3) < 0.01
        assert abs(cache.hit_rate - 2/3) < 0.01


class TestCachePerformance:
    """Verify cache efficiency improvements."""
    
    def test_soa_has_fewer_cache_misses(self):
        """SoA layout produces fewer cache misses than AoS."""
        records = [Record(i, float(i), f"cat_{i % 3}") for i in range(1000)]
        batch = PhaseBoundaryTransformer.aos_to_soa(records)
        
        cache = CacheSimulator()
        
        aos_misses = simulate_aos_access(records, cache)
        soa_misses = simulate_soa_access(batch, cache)
        
        # SoA should have significantly fewer misses
        assert soa_misses < aos_misses, \
            f"SoA should be more cache-friendly: AoS={aos_misses}, SoA={soa_misses}"
    
    def test_cache_improvement_ratio(self):
        """Verify cache improvement is substantial."""
        results = benchmark_layouts(10000)
        
        # SoA should have at least 2x fewer cache misses
        improvement = results['cache_improvement']
        assert improvement >= 2.0, \
            f"Expected at least 2x cache improvement, got {improvement:.1f}x"
    
    def test_sums_are_equal(self):
        """Both layouts compute same result."""
        results = benchmark_layouts(1000)
        
        assert abs(results['aos']['sum'] - results['soa']['sum']) < 0.001, \
            "AoS and SoA should produce identical sums"


class TestDataIntegrity:
    """Verify no data corruption occurs."""
    
    def test_negative_values_preserved(self):
        """Negative values roundtrip correctly."""
        original = [
            Record(1, -10.5, "A"),
            Record(2, -20.5, "B"),
        ]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert recovered[0].value == -10.5
        assert recovered[1].value == -20.5
    
    def test_large_values_preserved(self):
        """Large values roundtrip correctly."""
        original = [
            Record(1, 1e10, "A"),
            Record(2, 1e-10, "B"),
        ]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert abs(recovered[0].value - 1e10) < 1
        assert abs(recovered[1].value - 1e-10) < 1e-20
    
    def test_unicode_categories_preserved(self):
        """Unicode strings roundtrip correctly."""
        original = [
            Record(1, 10.5, "Category A 日本語"),
            Record(2, 20.5, "Category B 🎉"),
        ]
        batch = PhaseBoundaryTransformer.aos_to_soa(original)
        recovered = PhaseBoundaryTransformer.soa_to_aos(batch)
        
        assert recovered[0].category == "Category A 日本語"
        assert recovered[1].category == "Category B 🎉"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
