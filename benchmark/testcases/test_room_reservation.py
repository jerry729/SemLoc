import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.room_reservation import room_reservation
else:
    from programs.room_reservation import room_reservation


class TestBoundaryOverlapDetection:
    """Tests focusing on the exact boundary where intervals touch (share an endpoint)."""

    def test_new_interval_starts_exactly_where_existing_ends(self):
        """Adjacent intervals where the new interval starts at the existing interval's end should conflict."""
        existing = [(60, 120)]
        interval = (120, 150)
        accepted, schedule = room_reservation(existing, interval)
        # Intervals sharing endpoint (120) should be considered overlapping
        assert accepted is False

    def test_new_interval_ends_exactly_where_existing_starts(self):
        """Adjacent intervals where the new interval ends at the existing interval's start should conflict."""
        existing = [(120, 180)]
        interval = (100, 120)
        accepted, schedule = room_reservation(existing, interval)
        # Intervals sharing endpoint (120) should be considered overlapping
        assert accepted is False

    def test_touching_at_start_boundary_with_multiple_existing(self):
        """New interval ending exactly at an existing interval's start should conflict."""
        existing = [(60, 90), (200, 250)]
        interval = (180, 200)
        accepted, schedule = room_reservation(existing, interval)
        # Touches second interval at 200 — should be rejected
        assert accepted is False

    def test_touching_at_end_boundary_with_multiple_existing(self):
        """New interval starting exactly at an existing interval's end should conflict."""
        existing = [(60, 90), (200, 250)]
        interval = (90, 120)
        accepted, schedule = room_reservation(existing, interval)
        # Touches first interval at 90 — should be rejected
        assert accepted is False


class TestNonOverlappingReservations:
    """Tests that verify non-overlapping intervals are accepted correctly (pass on both versions)."""

    def test_empty_schedule_accepts_valid_interval(self):
        """A valid interval should be accepted when there are no existing reservations."""
        existing = []
        interval = (60, 120)
        accepted, schedule = room_reservation(existing, interval)
        assert accepted is True
        assert schedule == [(60, 120)]

    def test_clearly_separated_intervals(self):
        """Intervals with a clear gap between them should be accepted."""
        existing = [(60, 90)]
        interval = (120, 150)
        accepted, schedule = room_reservation(existing, interval)
        assert accepted is True
        assert schedule == [(60, 90), (120, 150)]

    def test_clearly_overlapping_intervals_rejected(self):
        """Intervals that clearly overlap should be rejected."""
        existing = [(60, 120)]
        interval = (100, 160)
        accepted, schedule = room_reservation(existing, interval)
        assert accepted is False
        assert schedule == [(60, 120)]

    def test_interval_inserted_in_sorted_order(self):
        """When accepted, the new interval should be inserted maintaining sorted order."""
        existing = [(30, 50), (200, 230)]
        interval = (100, 130)
        accepted, schedule = room_reservation(existing, interval)
        assert accepted is True
        assert schedule == [(30, 50), (100, 130), (200, 230)]


class TestValidationBehavior:
    """Tests for validation edge cases (pass on both versions)."""

    def test_invalid_interval_raises_value_error(self):
        """An interval where start >= end should raise ValueError."""
        with pytest.raises(ValueError):
            room_reservation([], (100, 50))

    def test_too_short_interval_raises_value_error(self):
        """An interval shorter than the minimum duration should raise ValueError."""
        with pytest.raises(ValueError):
            room_reservation([], (100, 110))