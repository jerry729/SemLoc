import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_training import schedule_training
else:
    from programs.schedule_training import schedule_training


class TestBoundaryOverlapDetection:
    """Tests for the exact boundary where intervals touch but do not overlap."""

    def test_new_interval_ends_exactly_at_existing_start(self):
        """An interval ending exactly where another begins should not be considered overlapping."""
        # existing: (10, 20), new: (5, 10) — they touch at point 10
        # Correct version: end(5,10)=10 < s=10 is False, but start=5 > e=20 is False => overlap detected
        # Wait, let me re-analyze the diff carefully.
        # Buggy:   not (end <= s or start >= e)  => overlap when end > s AND start < e
        # Correct: not (end < s or start > e)    => overlap when end >= s AND start <= e
        # So the correct version is MORE strict about overlaps (touching counts as overlap).
        # When end == s: buggy says no overlap (end <= s is True), correct says overlap (end < s is False, and start > e check matters)
        # Let me trace: existing=(10,20), new=(5,10)
        # Buggy:   not(10 <= 10 or 5 >= 20) = not(True or False) = not True = False => no conflict => inserted
        # Correct: not(10 < 10 or 5 > 20)   = not(False or False) = not False = True => conflict => rejected
        success, schedule = schedule_training([(10, 20)], (5, 10))
        assert success is False, "Intervals touching at a boundary point should be considered conflicting"

    def test_new_interval_starts_exactly_at_existing_end(self):
        """An interval starting exactly where another ends should be considered conflicting."""
        # existing: (5, 10), new: (10, 20)
        # Buggy:   not(20 <= 5 or 10 >= 10) = not(False or True) = not True = False => no conflict => inserted
        # Correct: not(20 < 5 or 10 > 10)   = not(False or False) = not False = True => conflict => rejected
        success, schedule = schedule_training([(5, 10)], (10, 20))
        assert success is False, "Intervals touching at a boundary point should be considered conflicting"

    def test_touching_at_boundary_with_multiple_existing(self):
        """When a new interval touches an existing one at exactly one endpoint among multiple slots."""
        # existing: (1, 5), (20, 30), new: (5, 10)
        # Buggy: checks (1,5): not(5<=1 or 5>=5) = not(False or True) = False => no conflict for this pair
        #        checks (20,30): not(10<=20 or 5>=30) = not(True or False) = False => no conflict => inserted
        # Correct: checks (1,5): not(5<1 or 5>5) = not(False or False) = True => conflict => rejected
        success, schedule = schedule_training([(1, 5), (20, 30)], (5, 10))
        assert success is False, "An interval touching the end of an existing session should conflict"

    def test_touching_at_start_boundary_with_multiple_existing(self):
        """New interval's end touches exactly the start of an existing interval among multiple."""
        # existing: (1, 5), (10, 20), new: (6, 10)
        # Buggy: checks (1,5): not(10<=1 or 6>=5) = not(False or True) = False => no conflict
        #        checks (10,20): not(10<=10 or 6>=20) = not(True or False) = False => no conflict => inserted
        # Correct: checks (10,20): not(10<10 or 6>20) = not(False or False) = True => conflict => rejected
        success, schedule = schedule_training([(1, 5), (10, 20)], (6, 10))
        assert success is False, "An interval whose end touches the start of an existing session should conflict"


class TestNonBoundaryBehavior:
    """Tests that pass on both buggy and correct versions — baseline behavior."""

    def test_insert_into_empty_schedule(self):
        """Inserting into an empty schedule should always succeed."""
        success, schedule = schedule_training([], (0, 5))
        assert success is True
        assert schedule == [(0, 5)]

    def test_clearly_overlapping_intervals_rejected(self):
        """An interval that clearly overlaps an existing one should be rejected."""
        success, schedule = schedule_training([(5, 15)], (10, 20))
        assert success is False
        assert schedule == [(5, 15)]

    def test_non_overlapping_intervals_accepted(self):
        """Intervals with clear gaps between them should be accepted."""
        success, schedule = schedule_training([(1, 5)], (10, 20))
        assert success is True
        assert (1, 5) in schedule
        assert (10, 20) in schedule

    def test_invalid_interval_raises_value_error(self):
        """An interval with start >= end should raise ValueError."""
        with pytest.raises(ValueError):
            schedule_training([], (10, 5))


class TestAdditionalBoundaryScenarios:
    """Additional boundary tests to ensure robust coverage of the touching-point behavior."""

    def test_exact_same_start_as_existing(self):
        """A new interval starting at the same point as an existing one clearly overlaps."""
        # Both versions should reject this
        success, schedule = schedule_training([(10, 20)], (10, 25))
        assert success is False

    def test_new_interval_end_equals_existing_start_with_gap_before(self):
        """New interval ending exactly at the start of existing, with nothing else around."""
        # existing: (100, 200), new: (50, 100)
        # Buggy: not(100<=100 or 50>=200) = not(True or False) = False => no conflict => inserted
        # Correct: not(100<100 or 50>200) = not(False or False) = True => conflict => rejected
        success, schedule = schedule_training([(100, 200)], (50, 100))
        assert success is False, "Touching at boundary should be a conflict"