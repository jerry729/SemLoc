import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.reserve_band import reserve_band
else:
    from programs.reserve_band import reserve_band


class TestReserveBandAdjacentBoundary:
    """Tests targeting the overlap detection boundary where candidate touches existing band edges."""

    def test_candidate_end_touches_existing_start(self):
        """Adjacent bands where candidate ends exactly where existing starts should be detected as overlapping."""
        existing = [(5.0, 10.0)]
        candidate = (2.0, 5.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(5.0, 10.0)]

    def test_candidate_start_touches_existing_end(self):
        """Adjacent bands where candidate starts exactly where existing ends should be detected as overlapping."""
        existing = [(1.0, 5.0)]
        candidate = (5.0, 8.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(1.0, 5.0)]

    def test_candidate_touches_existing_end_with_multiple_slots(self):
        """When candidate start equals the end of one existing slot, overlap should be detected."""
        existing = [(0.0, 3.0), (7.0, 10.0)]
        candidate = (3.0, 6.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(0.0, 3.0), (7.0, 10.0)]

    def test_candidate_end_touches_existing_start_with_multiple_slots(self):
        """When candidate end equals the start of one existing slot, overlap should be detected."""
        existing = [(0.0, 3.0), (7.0, 10.0)]
        candidate = (4.0, 7.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(0.0, 3.0), (7.0, 10.0)]

    def test_touching_at_single_point_both_sides(self):
        """Candidate that exactly fills the gap between two existing bands (touching both) should be rejected."""
        existing = [(0.0, 3.0), (6.0, 9.0)]
        candidate = (3.0, 6.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(0.0, 3.0), (6.0, 9.0)]


class TestReserveBandNonOverlapping:
    """Tests for cases that should succeed on both versions (no overlap at all)."""

    def test_no_existing_bands(self):
        """Reserving into an empty list should always succeed."""
        success, bands = reserve_band([], (1.0, 5.0))
        assert success is True
        assert bands == [(1.0, 5.0)]

    def test_candidate_clearly_before_existing(self):
        """Candidate fully before existing band with a gap should succeed."""
        existing = [(10.0, 20.0)]
        candidate = (1.0, 5.0)
        success, bands = reserve_band(existing, candidate)
        assert success is True
        assert (1.0, 5.0) in bands

    def test_candidate_clearly_after_existing(self):
        """Candidate fully after existing band with a gap should succeed."""
        existing = [(1.0, 5.0)]
        candidate = (10.0, 20.0)
        success, bands = reserve_band(existing, candidate)
        assert success is True
        assert (10.0, 20.0) in bands

    def test_clear_overlap_detected(self):
        """Candidate that clearly overlaps an existing band should be rejected by both versions."""
        existing = [(3.0, 8.0)]
        candidate = (5.0, 10.0)
        success, bands = reserve_band(existing, candidate)
        assert success is False
        assert bands == [(3.0, 8.0)]