import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_desk_slot import plan_desk_slot
else:
    from programs.plan_desk_slot import plan_desk_slot


# === Tests that PASS on both versions (baseline behavior) ===

def test_insert_into_empty_schedule():
    """A valid interval should be accepted into an empty schedule."""
    accepted, schedule = plan_desk_slot([], (1.0, 2.0))
    assert accepted is True
    assert schedule == [(1.0, 2.0)]


def test_clearly_overlapping_intervals_rejected():
    """An interval that clearly overlaps an existing booking should be rejected."""
    existing = [(2.0, 5.0)]
    accepted, schedule = plan_desk_slot(existing, (3.0, 6.0))
    assert accepted is False
    assert schedule == existing


def test_non_overlapping_well_separated():
    """An interval well-separated from existing bookings should be accepted."""
    existing = [(1.0, 2.0)]
    accepted, schedule = plan_desk_slot(existing, (5.0, 6.0))
    assert accepted is True
    assert (5.0, 6.0) in schedule


def test_invalid_interval_raises():
    """An interval where start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        plan_desk_slot([], (5.0, 3.0))


# === Tests that FAIL on buggy, PASS on correct (targeting adjacency boundary) ===

def test_adjacent_new_starts_where_existing_ends():
    """When new interval starts exactly where an existing one ends, they are adjacent and should conflict."""
    existing = [(2.0, 4.0)]
    # New interval starts at 4.0, exactly where existing ends
    accepted, schedule = plan_desk_slot(existing, (4.0, 5.0))
    assert accepted is False
    assert schedule == existing


def test_adjacent_new_ends_where_existing_starts():
    """When new interval ends exactly where an existing one starts, they are adjacent and should conflict."""
    existing = [(5.0, 7.0)]
    # New interval ends at 5.0, exactly where existing starts
    accepted, schedule = plan_desk_slot(existing, (4.0, 5.0))
    assert accepted is False
    assert schedule == existing


def test_adjacent_slot_between_two_existing():
    """A new interval that is adjacent to two existing bookings (touching both) should be rejected."""
    existing = [(1.0, 3.0), (5.0, 7.0)]
    # New interval [3.0, 5.0) touches end of first and start of second
    accepted, schedule = plan_desk_slot(existing, (3.0, 5.0))
    assert accepted is False
    assert schedule == existing


def test_adjacent_back_to_back_chain():
    """Building a chain of back-to-back bookings should fail because adjacency is a conflict."""
    existing = [(8.0, 10.0)]
    # Try to book [10.0, 11.0) — starts exactly where existing ends
    accepted, schedule = plan_desk_slot(existing, (10.0, 11.0))
    assert accepted is False
    assert schedule == existing


def test_adjacent_with_multiple_existing_only_one_touches():
    """When only one of several existing slots is adjacent, the new interval should still be rejected."""
    existing = [(1.0, 2.0), (5.0, 6.0), (9.0, 10.0)]
    # New interval ends exactly at 9.0, touching the third existing slot
    accepted, schedule = plan_desk_slot(existing, (8.0, 9.0))
    assert accepted is False
    assert schedule == existing


def test_non_adjacent_gap_between_slots_accepted():
    """An interval with a clear gap (not adjacent) from all existing slots should be accepted."""
    existing = [(1.0, 2.0), (5.0, 6.0)]
    # New interval [3.0, 4.0) has gaps on both sides — no adjacency
    accepted, schedule = plan_desk_slot(existing, (3.0, 4.0))
    assert accepted is True
    assert (3.0, 4.0) in schedule
    assert len(schedule) == 3