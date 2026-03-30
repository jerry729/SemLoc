import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.machine_booking import machine_booking
else:
    from programs.machine_booking import machine_booking


# --- Tests that PASS on both versions (baseline behavior) ---

def test_no_conflict_gap_between_bookings():
    """A window that fits in a gap between existing bookings should be accepted."""
    timeline = [(1, 3), (7, 10)]
    accepted, result = machine_booking(timeline, (4, 6))
    assert accepted is True
    assert (4, 6) in result
    assert len(result) == 3


def test_overlapping_window_rejected():
    """A window that clearly overlaps an existing booking should be rejected."""
    timeline = [(5, 10)]
    accepted, result = machine_booking(timeline, (7, 12))
    assert accepted is False
    assert result == [(5, 10)]


def test_empty_timeline_accepts_booking():
    """A booking on an empty timeline should always be accepted."""
    timeline = []
    accepted, result = machine_booking(timeline, (3, 8))
    assert accepted is True
    assert result == [(3, 8)]


def test_invalid_window_raises_value_error():
    """A window where start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        machine_booking([], (5, 5))
    with pytest.raises(ValueError):
        machine_booking([], (10, 3))


# --- Tests that FAIL on buggy, PASS on correct (touching boundary) ---

def test_adjacent_window_end_touches_existing_start():
    """A window whose end equals an existing booking's start should be treated as a conflict."""
    timeline = [(5, 10)]
    accepted, result = machine_booking(timeline, (2, 5))
    assert accepted is False
    assert result == [(5, 10)]


def test_adjacent_window_start_touches_existing_end():
    """A window whose start equals an existing booking's end should be treated as a conflict."""
    timeline = [(2, 5)]
    accepted, result = machine_booking(timeline, (5, 8))
    assert accepted is False
    assert result == [(2, 5)]


def test_touching_both_sides_between_two_bookings():
    """A window that touches both adjacent bookings at their boundaries should be rejected."""
    timeline = [(1, 3), (7, 10)]
    accepted, result = machine_booking(timeline, (3, 7))
    assert accepted is False
    assert result == [(1, 3), (7, 10)]


def test_adjacent_touching_with_multiple_existing_bookings():
    """When multiple bookings exist, a window touching any one's boundary should be rejected."""
    timeline = [(0, 2), (4, 6), (8, 10)]
    # Window end touches start of (4, 6)
    accepted, result = machine_booking(timeline, (3, 4))
    assert accepted is False
    assert result == [(0, 2), (4, 6), (8, 10)]


def test_adjacent_touching_end_boundary_of_last_booking():
    """A window whose start equals the end of the last booking should be rejected."""
    timeline = [(0, 5)]
    accepted, result = machine_booking(timeline, (5, 9))
    assert accepted is False
    assert result == [(0, 5)]


def test_touching_single_point_boundary():
    """A minimal-duration window that touches an existing booking boundary should be rejected."""
    timeline = [(10, 20)]
    accepted, result = machine_booking(timeline, (9, 10))
    assert accepted is False
    assert result == [(10, 20)]