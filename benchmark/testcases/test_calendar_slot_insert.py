import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calendar_slot_insert import calendar_slot_insert
else:
    from programs.calendar_slot_insert import calendar_slot_insert


# --- Tests that FAIL on buggy, PASS on correct (adjacent slot rejection) ---

def test_adjacent_slot_new_ends_where_existing_starts():
    """When a new slot ends exactly where an existing slot starts, they are adjacent and should conflict."""
    existing = [(120, 180)]
    slot = (60, 120)  # new slot ends at 120, existing starts at 120
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(120, 180)]


def test_adjacent_slot_new_starts_where_existing_ends():
    """When a new slot starts exactly where an existing slot ends, they are adjacent and should conflict."""
    existing = [(60, 120)]
    slot = (120, 180)  # new slot starts at 120, existing ends at 120
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(60, 120)]


def test_adjacent_slot_between_two_existing():
    """A slot that is exactly adjacent to two existing slots (touching both boundaries) should conflict."""
    existing = [(0, 60), (120, 180)]
    slot = (60, 120)  # touches end of first and start of second
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(0, 60), (120, 180)]


def test_adjacent_slot_touching_end_boundary():
    """A slot whose start equals an existing slot's end should be rejected as adjacent/conflicting."""
    existing = [(300, 360)]
    slot = (360, 420)
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(300, 360)]


def test_adjacent_slot_touching_start_boundary():
    """A slot whose end equals an existing slot's start should be rejected as adjacent/conflicting."""
    existing = [(480, 540)]
    slot = (420, 480)
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(480, 540)]


# --- Tests that PASS on BOTH versions (baseline behavior) ---

def test_insert_into_empty_schedule():
    """Inserting a valid slot into an empty schedule should always succeed."""
    existing = []
    slot = (60, 120)
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is True
    assert schedule == [(60, 120)]


def test_overlapping_slot_rejected():
    """A slot that overlaps with an existing slot (not just adjacent) should be rejected."""
    existing = [(100, 200)]
    slot = (150, 250)
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is False
    assert schedule == [(100, 200)]


def test_non_overlapping_non_adjacent_slot_inserted():
    """A slot with a gap between it and existing slots should be successfully inserted."""
    existing = [(60, 120)]
    slot = (200, 260)  # clear gap, no adjacency
    inserted, schedule = calendar_slot_insert(existing, slot)
    assert inserted is True
    assert schedule == [(60, 120), (200, 260)]


def test_invalid_slot_raises_error():
    """A slot where start >= end should raise a ValueError."""
    with pytest.raises(ValueError):
        calendar_slot_insert([], (120, 60))