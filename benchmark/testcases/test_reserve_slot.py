import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.reserve_slot import reserve_slot
else:
    from programs.reserve_slot import reserve_slot


class TestBoundaryOverlap:
    """Tests targeting the exact boundary where candidate end == existing start
    or candidate start == existing end (touching slots)."""

    def test_candidate_end_touches_existing_start(self):
        """Slots that share a single boundary point (candidate ends where existing starts) should be considered overlapping."""
        existing = [(5, 10)]
        candidate = (3, 5)  # candidate end == existing start
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(5, 10)]

    def test_candidate_start_touches_existing_end(self):
        """Slots that share a single boundary point (candidate starts where existing ends) should be considered overlapping."""
        existing = [(1, 5)]
        candidate = (5, 8)  # candidate start == existing end
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(1, 5)]

    def test_existing_end_equals_candidate_start_multiple_existing(self):
        """When candidate start exactly equals an existing slot's end, it should conflict."""
        existing = [(0, 3), (10, 15)]
        candidate = (3, 7)  # candidate start == first existing end
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(0, 3), (10, 15)]

    def test_candidate_end_equals_existing_start_multiple_existing(self):
        """When candidate end exactly equals an existing slot's start, it should conflict."""
        existing = [(0, 3), (10, 15)]
        candidate = (7, 10)  # candidate end == second existing start
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(0, 3), (10, 15)]

    def test_touching_both_sides(self):
        """A candidate that exactly fills a gap between two existing slots (touching both) should conflict."""
        existing = [(0, 5), (10, 15)]
        candidate = (5, 10)  # touches both existing slots at boundaries
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(0, 5), (10, 15)]


class TestNonOverlapping:
    """Tests for slots that are clearly separated and should be reserved successfully."""

    def test_no_existing_slots(self):
        """A candidate with no existing slots should always be reserved."""
        reserved, schedule = reserve_slot([], (1, 5))
        assert reserved is True
        assert schedule == [(1, 5)]

    def test_candidate_well_before_existing(self):
        """A candidate entirely before existing slots should be reserved."""
        existing = [(10, 15)]
        candidate = (1, 5)
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is True
        assert schedule == [(1, 5), (10, 15)]

    def test_candidate_well_after_existing(self):
        """A candidate entirely after existing slots should be reserved."""
        existing = [(1, 5)]
        candidate = (10, 15)
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is True
        assert schedule == [(1, 5), (10, 15)]

    def test_clear_overlap_rejected(self):
        """A candidate that clearly overlaps an existing slot should be rejected."""
        existing = [(5, 10)]
        candidate = (7, 12)
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(5, 10)]


class TestEdgeCases:
    """Additional edge case tests."""

    def test_invalid_candidate_raises_value_error(self):
        """A candidate where start >= end should raise ValueError."""
        with pytest.raises(ValueError):
            reserve_slot([], (5, 5))

    def test_single_unit_touching_at_boundary(self):
        """A single-unit candidate whose end touches an existing slot's start should conflict."""
        existing = [(5, 10)]
        candidate = (4, 5)  # end exactly at existing start
        reserved, schedule = reserve_slot(existing, candidate)
        assert reserved is False
        assert schedule == [(5, 10)]