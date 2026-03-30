import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_pickup import schedule_pickup
else:
    from programs.schedule_pickup import schedule_pickup


# --- Tests that PASS on both versions (baseline behavior) ---

def test_empty_timeline_accepts_booking():
    """A booking into an empty timeline should always succeed."""
    success, result = schedule_pickup([], (5, 10))
    assert success is True
    assert result == [(5, 10)]


def test_clearly_overlapping_windows_rejected():
    """A new window that clearly overlaps an existing booking should be rejected."""
    timeline = [(10, 20)]
    success, result = schedule_pickup(timeline, (15, 25))
    assert success is False
    assert result is timeline


def test_non_overlapping_windows_accepted():
    """Windows with a gap between them should be accepted without conflict."""
    timeline = [(10, 20)]
    success, result = schedule_pickup(timeline, (25, 30))
    assert success is True
    assert (25, 30) in result


def test_invalid_window_raises_value_error():
    """A window with zero or negative duration should raise ValueError."""
    with pytest.raises(ValueError):
        schedule_pickup([], (10, 10))


# --- Tests that FAIL on buggy, PASS on correct ---

def test_adjacent_window_end_touches_existing_start():
    """A window whose end equals an existing booking's start should be treated as a conflict (touching boundary)."""
    timeline = [(10, 20)]
    # New window (5, 10) — end of new == start of existing
    success, result = schedule_pickup(timeline, (5, 10))
    assert success is False
    assert result is timeline


def test_adjacent_window_start_touches_existing_end():
    """A window whose start equals an existing booking's end should be treated as a conflict (touching boundary)."""
    timeline = [(10, 20)]
    # New window (20, 25) — start of new == end of existing
    success, result = schedule_pickup(timeline, (20, 25))
    assert success is False
    assert result is timeline


def test_both_boundaries_touch_existing_slots():
    """A window that exactly fills the gap between two existing slots (touching both) should be rejected."""
    timeline = [(5, 10), (20, 25)]
    # New window (10, 20) — touches end of first and start of second
    success, result = schedule_pickup(timeline, (10, 20))
    assert success is False
    assert result is timeline


def test_adjacent_touch_with_multiple_existing_bookings():
    """When multiple bookings exist, a window touching any one boundary should be rejected."""
    timeline = [(0, 5), (10, 15), (20, 25)]
    # New window (15, 20) — start touches end of (10,15), end touches start of (20,25)
    success, result = schedule_pickup(timeline, (15, 20))
    assert success is False
    assert result is timeline


def test_adjacent_single_point_touch_at_end():
    """A window whose start exactly equals the end of the only existing booking is a boundary conflict."""
    timeline = [(100, 200)]
    success, result = schedule_pickup(timeline, (200, 300))
    assert success is False
    assert result is timeline


def test_adjacent_single_point_touch_at_start():
    """A window whose end exactly equals the start of the only existing booking is a boundary conflict."""
    timeline = [(100, 200)]
    success, result = schedule_pickup(timeline, (50, 100))
    assert success is False
    assert result is timeline