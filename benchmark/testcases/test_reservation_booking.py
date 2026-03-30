import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.reservation_booking import reservation_booking
else:
    from programs.reservation_booking import reservation_booking


# === Tests that FAIL on buggy, PASS on correct (adjacent boundary cases) ===

def test_new_interval_ends_exactly_at_existing_start():
    """Adjacent intervals where new interval's end equals existing interval's start should conflict."""
    existing = [(5, 10)]
    booked, schedule = reservation_booking(existing, (2, 5))
    assert booked is False
    assert schedule == existing


def test_new_interval_starts_exactly_at_existing_end():
    """Adjacent intervals where new interval's start equals existing interval's end should conflict."""
    existing = [(5, 10)]
    booked, schedule = reservation_booking(existing, (10, 15))
    assert booked is False
    assert schedule == existing


def test_adjacent_touching_at_boundary_with_multiple_existing():
    """When new interval touches exactly at the end of one of multiple existing intervals, it should conflict."""
    existing = [(0, 5), (10, 15)]
    booked, schedule = reservation_booking(existing, (5, 8))
    assert booked is False
    assert schedule == existing


def test_adjacent_touching_at_start_of_second_existing():
    """When new interval's end touches exactly the start of a later existing interval, it should conflict."""
    existing = [(0, 3), (10, 15)]
    booked, schedule = reservation_booking(existing, (7, 10))
    assert booked is False
    assert schedule == existing


def test_new_interval_boundaries_touch_both_neighbors():
    """When new interval is sandwiched exactly between two existing intervals, touching both, it should conflict."""
    existing = [(0, 5), (10, 15)]
    booked, schedule = reservation_booking(existing, (5, 10))
    assert booked is False
    assert schedule == existing


# === Tests that PASS on BOTH versions (baseline behavior) ===

def test_no_overlap_with_gap():
    """A new interval with clear gaps from all existing intervals should be booked successfully."""
    existing = [(0, 3), (10, 15)]
    booked, schedule = reservation_booking(existing, (5, 8))
    assert booked is True
    assert (5, 8) in schedule
    assert len(schedule) == 3


def test_true_overlap_rejected():
    """A new interval that truly overlaps an existing interval should be rejected."""
    existing = [(5, 10)]
    booked, schedule = reservation_booking(existing, (7, 12))
    assert booked is False
    assert schedule == existing


def test_booking_into_empty_schedule():
    """Booking into an empty schedule should always succeed."""
    existing = []
    booked, schedule = reservation_booking(existing, (0, 5))
    assert booked is True
    assert schedule == [(0, 5)]


def test_invalid_interval_raises_error():
    """An interval where start >= end should raise a ValueError."""
    with pytest.raises(ValueError):
        reservation_booking([], (10, 5))