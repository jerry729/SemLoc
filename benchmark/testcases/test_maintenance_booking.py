import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.maintenance_booking import maintenance_booking
else:
    from programs.maintenance_booking import maintenance_booking


def test_adjacent_window_end_touches_existing_start():
    """Windows that share an endpoint (new end == existing start) should be treated as conflicts."""
    timeline = [(5, 10)]
    success, result = maintenance_booking(timeline, (2, 5))
    assert success is False
    assert result == timeline


def test_adjacent_window_start_touches_existing_end():
    """Windows that share an endpoint (new start == existing end) should be treated as conflicts."""
    timeline = [(1, 5)]
    success, result = maintenance_booking(timeline, (5, 8))
    assert success is False
    assert result == timeline


def test_adjacent_touching_at_boundary_multiple_existing():
    """When the new window's end exactly equals one existing window's start, it should conflict."""
    timeline = [(3, 6), (10, 15)]
    success, result = maintenance_booking(timeline, (6, 10))
    assert success is False
    assert result == timeline


def test_adjacent_touching_first_slot_boundary():
    """A new window ending exactly at the first existing window's start is a conflict."""
    timeline = [(10, 20), (30, 40)]
    success, result = maintenance_booking(timeline, (5, 10))
    assert success is False
    assert result == timeline


def test_adjacent_touching_last_slot_boundary():
    """A new window starting exactly at the last existing window's end is a conflict."""
    timeline = [(10, 20), (30, 40)]
    success, result = maintenance_booking(timeline, (40, 50))
    assert success is False
    assert result == timeline


def test_no_overlap_with_gap_between_windows():
    """Non-adjacent windows with a gap between them should be successfully booked."""
    timeline = [(1, 3)]
    success, result = maintenance_booking(timeline, (4, 6))
    assert success is True
    assert result == [(1, 3), (4, 6)]


def test_clear_overlap_rejected():
    """A window that clearly overlaps an existing booking should be rejected."""
    timeline = [(5, 10)]
    success, result = maintenance_booking(timeline, (7, 12))
    assert success is False
    assert result == timeline


def test_booking_into_empty_timeline():
    """Booking into an empty timeline should always succeed."""
    timeline = []
    success, result = maintenance_booking(timeline, (1, 5))
    assert success is True
    assert result == [(1, 5)]


def test_invalid_window_raises_value_error():
    """A window where start >= end should raise a ValueError."""
    with pytest.raises(ValueError):
        maintenance_booking([], (5, 5))


def test_adjacent_single_unit_windows_touching():
    """Two single-unit windows that touch at a point should conflict."""
    timeline = [(1, 2)]
    success, result = maintenance_booking(timeline, (2, 3))
    assert success is False
    assert result == timeline