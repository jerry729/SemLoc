import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_car import schedule_car
else:
    from programs.schedule_car import schedule_car


def test_adjacent_window_end_equals_existing_start():
    """A new booking whose end time equals an existing booking's start time should be rejected."""
    timeline = [(5, 10)]
    accepted, result = schedule_car(timeline, (3, 5))
    assert accepted is False
    assert result == [(5, 10)]


def test_adjacent_window_start_equals_existing_end():
    """A new booking whose start time equals an existing booking's end time should be rejected."""
    timeline = [(5, 10)]
    accepted, result = schedule_car(timeline, (10, 15))
    assert accepted is False
    assert result == [(5, 10)]


def test_adjacent_on_both_sides():
    """A new booking that touches existing bookings on both sides should be rejected."""
    timeline = [(1, 5), (10, 15)]
    accepted, result = schedule_car(timeline, (5, 10))
    assert accepted is False
    assert result == [(1, 5), (10, 15)]


def test_adjacent_end_equals_start_different_values():
    """A new booking ending exactly at an existing booking's start should be rejected."""
    timeline = [(20, 30)]
    accepted, result = schedule_car(timeline, (15, 20))
    assert accepted is False
    assert result == [(20, 30)]


def test_non_overlapping_with_gap_accepted():
    """A new booking with a clear gap from existing bookings should be accepted."""
    timeline = [(5, 10)]
    accepted, result = schedule_car(timeline, (12, 15))
    assert accepted is True
    assert result == [(5, 10), (12, 15)]


def test_empty_timeline_accepted():
    """A booking into an empty timeline should always be accepted."""
    timeline = []
    accepted, result = schedule_car(timeline, (1, 5))
    assert accepted is True
    assert result == [(1, 5)]


def test_overlapping_booking_rejected():
    """A booking that clearly overlaps an existing one should be rejected."""
    timeline = [(5, 10)]
    accepted, result = schedule_car(timeline, (7, 12))
    assert accepted is False
    assert result == [(5, 10)]


def test_invalid_window_raises_error():
    """A window where start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        schedule_car([], (10, 5))


def test_multiple_adjacent_bookings_all_rejected():
    """New booking touching any of multiple existing bookings should be rejected."""
    timeline = [(0, 3), (7, 10), (15, 20)]
    # Touching the end of (0,3)
    accepted1, _ = schedule_car(timeline, (3, 5))
    assert accepted1 is False
    # Touching the start of (7,10)
    accepted2, _ = schedule_car(timeline, (5, 7))
    assert accepted2 is False
    # Touching the start of (15,20)
    accepted3, _ = schedule_car(timeline, (13, 15))
    assert accepted3 is False


def test_booking_well_inside_gap_accepted():
    """A booking that fits well within a gap between existing bookings should be accepted."""
    timeline = [(0, 5), (20, 25)]
    accepted, result = schedule_car(timeline, (10, 15))
    assert accepted is True
    assert result == [(0, 5), (10, 15), (20, 25)]