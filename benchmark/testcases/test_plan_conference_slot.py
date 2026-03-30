import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_conference_slot import plan_conference_slot
else:
    from programs.plan_conference_slot import plan_conference_slot


# === Tests that PASS on correct, FAIL on buggy ===
# The bug: overlaps uses `<=` and `>=` instead of `<` and `>`
# This means adjacent/touching slots (where one ends exactly where another starts)
# are NOT detected as overlapping in the buggy version, but SHOULD be in the correct version.

class TestAdjacentSlotConflict:
    """Tests for slots that share an exact boundary point."""

    def test_candidate_starts_where_existing_ends(self):
        """A candidate starting exactly when an existing slot ends should be detected as overlapping."""
        existing = [(60, 120)]  # 1:00 - 2:00
        candidate = (120, 180)  # 2:00 - 3:00 — touches at 120
        accepted, schedule = plan_conference_slot(existing, candidate)
        # In correct version, touching slots overlap, so accepted should be False
        assert accepted is False

    def test_candidate_ends_where_existing_starts(self):
        """A candidate ending exactly when an existing slot starts should be detected as overlapping."""
        existing = [(120, 180)]  # 2:00 - 3:00
        candidate = (60, 120)   # 1:00 - 2:00 — touches at 120
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is False

    def test_touching_at_single_point_multiple_existing(self):
        """When candidate touches one of multiple existing slots at a boundary, it should conflict."""
        existing = [(0, 60), (180, 240)]
        candidate = (60, 120)  # touches first slot at 60
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is False

    def test_touching_last_existing_slot(self):
        """Candidate touching the end of the last existing slot should conflict."""
        existing = [(0, 30), (30, 60)]
        candidate = (60, 90)  # touches second slot at 60
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is False


# === Tests that PASS on BOTH versions (baseline behavior) ===

class TestBasicBehavior:
    """Baseline tests that verify fundamental behavior on both versions."""

    def test_no_existing_slots(self):
        """Adding a candidate to an empty schedule should always succeed."""
        existing = []
        candidate = (60, 120)
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is True
        assert schedule == [(60, 120)]

    def test_clearly_overlapping_slots(self):
        """A candidate that clearly overlaps an existing slot should be rejected."""
        existing = [(60, 120)]
        candidate = (90, 150)
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is False
        assert schedule == [(60, 120)]

    def test_clearly_non_overlapping_slots(self):
        """A candidate with a gap from all existing slots should be accepted."""
        existing = [(60, 120)]
        candidate = (180, 240)  # well after existing slot
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is True
        assert schedule == [(60, 120), (180, 240)]

    def test_invalid_candidate_raises_valueerror(self):
        """A candidate where start >= end should raise ValueError."""
        existing = []
        with pytest.raises(ValueError):
            plan_conference_slot(existing, (120, 60))


# === Additional boundary tests ===

class TestNearBoundary:
    """Tests near the touching boundary to ensure correct behavior."""

    def test_one_minute_gap_no_conflict(self):
        """Slots separated by 1 minute should not conflict."""
        existing = [(60, 119)]
        candidate = (120, 180)
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is True

    def test_candidate_contained_within_existing(self):
        """A candidate fully inside an existing slot should conflict."""
        existing = [(60, 180)]
        candidate = (90, 150)
        accepted, schedule = plan_conference_slot(existing, candidate)
        assert accepted is False