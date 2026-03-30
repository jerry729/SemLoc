import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_window import schedule_window
else:
    from programs.schedule_window import schedule_window


class TestBoundaryOverlapDetection:
    """Tests for overlap detection at exact boundary points where intervals touch."""

    def test_new_interval_ends_exactly_at_existing_start(self):
        """An interval ending exactly when another begins should be detected as overlapping."""
        # existing: (200, 400), new interval ends at 200 exactly
        existing = [(200, 400)]
        accepted, calendar = schedule_window(existing, (100, 200))
        # In the correct version, end == s (200 == 200) means overlap
        assert accepted is False
        assert calendar == existing

    def test_new_interval_starts_exactly_at_existing_end(self):
        """An interval starting exactly when another ends should be detected as overlapping."""
        # existing: (100, 200), new interval starts at 200 exactly
        existing = [(100, 200)]
        accepted, calendar = schedule_window(existing, (200, 400))
        # In the correct version, start == e (200 == 200) means overlap
        assert accepted is False
        assert calendar == existing

    def test_adjacent_touching_at_both_boundaries(self):
        """When the new interval touches an existing one at the start boundary, it should conflict."""
        existing = [(500, 600)]
        accepted, calendar = schedule_window(existing, (400, 500))
        # end of new (500) == start of existing (500) -> overlap in correct version
        assert accepted is False
        assert calendar == existing

    def test_new_interval_starts_at_existing_end_multiple_slots(self):
        """With multiple existing slots, touching the end of one should be a conflict."""
        existing = [(100, 200), (300, 400)]
        accepted, calendar = schedule_window(existing, (200, 300))
        # start of new (200) == end of first existing (200) -> overlap
        # OR end of new (300) == start of second existing (300) -> overlap
        assert accepted is False
        assert calendar == existing

    def test_touching_end_boundary_with_single_existing(self):
        """A new interval whose start equals an existing interval's end is an overlap."""
        existing = [(1000, 2000)]
        accepted, calendar = schedule_window(existing, (2000, 3000))
        assert accepted is False
        assert calendar == existing


class TestNonBoundaryBehavior:
    """Tests that pass on both versions — verifying core scheduling logic."""

    def test_no_existing_slots_accepts_valid_interval(self):
        """A valid interval should be accepted when no existing slots exist."""
        accepted, calendar = schedule_window([], (100, 200))
        assert accepted is True
        assert calendar == [(100, 200)]

    def test_clear_overlap_is_rejected(self):
        """An interval that clearly overlaps an existing one should be rejected."""
        existing = [(100, 300)]
        accepted, calendar = schedule_window(existing, (150, 250))
        assert accepted is False
        assert calendar == existing

    def test_non_overlapping_interval_accepted(self):
        """An interval with a clear gap from all existing slots should be accepted."""
        existing = [(100, 200)]
        accepted, calendar = schedule_window(existing, (300, 400))
        assert accepted is True
        assert (300, 400) in calendar

    def test_invalid_interval_raises_value_error(self):
        """An interval where start >= end should raise ValueError."""
        with pytest.raises(ValueError):
            schedule_window([], (200, 100))