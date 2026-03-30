import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_call import schedule_call
else:
    from programs.schedule_call import schedule_call


class TestAdjacentSlotsBoundary:
    """Tests for the exact boundary where one slot ends and another begins."""

    def test_candidate_starts_exactly_where_existing_ends(self):
        """Two slots that are exactly adjacent (touching at a single point) should be treated as overlapping."""
        existing = [(60, 120)]
        candidate = (120, 180)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False, "Candidate starting exactly at existing end should conflict"

    def test_candidate_ends_exactly_where_existing_starts(self):
        """A candidate ending exactly where an existing slot starts should be treated as overlapping."""
        existing = [(120, 180)]
        candidate = (60, 120)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False, "Candidate ending exactly at existing start should conflict"

    def test_adjacent_touching_multiple_existing(self):
        """Candidate touching the start of the first existing slot should conflict."""
        existing = [(100, 150), (200, 250)]
        candidate = (50, 100)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False, "Candidate ending exactly at first existing start should conflict"

    def test_adjacent_touching_second_existing(self):
        """Candidate starting exactly where the second existing slot ends should conflict."""
        existing = [(100, 150), (200, 250)]
        candidate = (250, 300)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False, "Candidate starting exactly at second existing end should conflict"


class TestNonOverlapping:
    """Tests for slots that are clearly separated and should be accepted."""

    def test_no_existing_slots(self):
        """Scheduling into an empty calendar should always succeed."""
        accepted, schedule = schedule_call([], (60, 120))
        assert accepted is True
        assert schedule == [(60, 120)]

    def test_candidate_well_before_existing(self):
        """A candidate well before any existing slot should be accepted."""
        existing = [(200, 300)]
        candidate = (10, 50)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is True
        assert candidate in schedule

    def test_candidate_well_after_existing(self):
        """A candidate well after any existing slot should be accepted."""
        existing = [(60, 120)]
        candidate = (200, 300)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is True
        assert candidate in schedule

    def test_candidate_between_existing_with_gaps(self):
        """A candidate fitting in a gap between two existing slots should be accepted."""
        existing = [(60, 100), (200, 300)]
        candidate = (120, 180)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is True
        assert schedule == [(60, 100), (120, 180), (200, 300)]


class TestClearOverlap:
    """Tests for clearly overlapping slots that should be rejected by both versions."""

    def test_partial_overlap(self):
        """A candidate partially overlapping an existing slot should be rejected."""
        existing = [(60, 120)]
        candidate = (100, 160)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False

    def test_candidate_contained_within_existing(self):
        """A candidate fully contained within an existing slot should be rejected."""
        existing = [(60, 180)]
        candidate = (80, 150)
        accepted, schedule = schedule_call(existing, candidate)
        assert accepted is False