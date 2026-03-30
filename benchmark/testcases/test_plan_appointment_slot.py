import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_appointment_slot import plan_appointment_slot
else:
    from programs.plan_appointment_slot import plan_appointment_slot


# --- Tests that PASS on both versions (baseline behavior) ---

def test_no_conflict_with_gap():
    """A new window placed in a clear gap between existing slots should succeed."""
    timeline = [(1, 3), (7, 10)]
    success, result = plan_appointment_slot(timeline, (4, 6))
    assert success is True
    assert (4, 6) in result
    assert len(result) == 3


def test_clear_overlap_rejected():
    """A window that clearly overlaps an existing slot should be rejected."""
    timeline = [(5, 10)]
    success, result = plan_appointment_slot(timeline, (7, 12))
    assert success is False


def test_empty_timeline_accepts():
    """Any valid window should be accepted into an empty timeline."""
    timeline = []
    success, result = plan_appointment_slot(timeline, (3, 7))
    assert success is True
    assert result == [(3, 7)]


def test_invalid_window_raises():
    """A window with start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        plan_appointment_slot([], (5, 5))
    with pytest.raises(ValueError):
        plan_appointment_slot([], (10, 3))


# --- Tests that FAIL on buggy, PASS on correct ---

def test_adjacent_window_end_touches_existing_start():
    """A window whose end equals an existing slot's start should be rejected as overlapping."""
    timeline = [(5, 10)]
    success, result = plan_appointment_slot(timeline, (2, 5))
    assert success is False
    assert len(result) == 1


def test_adjacent_window_start_touches_existing_end():
    """A window whose start equals an existing slot's end should be rejected as overlapping."""
    timeline = [(1, 5)]
    success, result = plan_appointment_slot(timeline, (5, 8))
    assert success is False
    assert len(result) == 1


def test_adjacent_touching_both_sides():
    """A window that touches existing slots on both sides should be rejected."""
    timeline = [(1, 3), (7, 10)]
    success, result = plan_appointment_slot(timeline, (3, 7))
    assert success is False
    assert len(result) == 2


def test_adjacent_single_point_touch_at_boundary():
    """A unit-length window touching an existing slot endpoint should be rejected."""
    timeline = [(10, 15)]
    success, result = plan_appointment_slot(timeline, (9, 10))
    assert success is False
    assert len(result) == 1


def test_multiple_slots_touching_chain():
    """Inserting a slot that would touch an existing slot in a chain should be rejected."""
    timeline = [(0, 2), (4, 6), (8, 10)]
    # Window (6, 8) touches slot (4,6) at start=6 and slot (8,10) at end=8
    success, result = plan_appointment_slot(timeline, (6, 8))
    assert success is False
    assert len(result) == 3


def test_window_end_touches_existing_start_large_values():
    """Adjacent touching rejection should work with larger coordinate values."""
    timeline = [(100, 200)]
    success, result = plan_appointment_slot(timeline, (50, 100))
    assert success is False
    assert len(result) == 1