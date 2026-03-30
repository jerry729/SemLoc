import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_upgrade_slot import plan_upgrade_slot
else:
    from programs.plan_upgrade_slot import plan_upgrade_slot


def test_no_overlap_gap_between_slots():
    """Non-overlapping windows with a gap should be successfully placed."""
    timeline = [(1, 3)]
    success, result = plan_upgrade_slot(timeline, (5, 7))
    assert success is True
    assert (5, 7) in result


def test_clear_overlap_rejected():
    """A window that clearly overlaps an existing slot should be rejected."""
    timeline = [(3, 8)]
    success, result = plan_upgrade_slot(timeline, (5, 10))
    assert success is False
    assert result == [(3, 8)]


def test_empty_timeline_accepts_any_valid_window():
    """Any valid window should be accepted into an empty timeline."""
    timeline = []
    success, result = plan_upgrade_slot(timeline, (2, 5))
    assert success is True
    assert result == [(2, 5)]


def test_invalid_window_raises_value_error():
    """A window where start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        plan_upgrade_slot([], (5, 3))


def test_adjacent_window_end_touches_existing_start():
    """A window whose end equals an existing slot's start is an adjacent/touching boundary and should be rejected."""
    timeline = [(5, 10)]
    success, result = plan_upgrade_slot(timeline, (2, 5))
    assert success is False
    assert result == [(5, 10)]


def test_adjacent_window_start_touches_existing_end():
    """A window whose start equals an existing slot's end is an adjacent/touching boundary and should be rejected."""
    timeline = [(1, 5)]
    success, result = plan_upgrade_slot(timeline, (5, 8))
    assert success is False
    assert result == [(1, 5)]


def test_adjacent_both_sides_touching():
    """A window fitting exactly between two existing slots with touching boundaries should be rejected."""
    timeline = [(1, 3), (7, 10)]
    success, result = plan_upgrade_slot(timeline, (3, 7))
    assert success is False
    assert result == [(1, 3), (7, 10)]


def test_adjacent_window_end_touches_existing_start_exact_integers():
    """When the new window ends exactly where an existing one starts (integer boundary), it should conflict."""
    timeline = [(10, 20)]
    success, result = plan_upgrade_slot(timeline, (5, 10))
    assert success is False
    assert result == [(10, 20)]


def test_non_adjacent_with_gap_of_one():
    """A window that has a gap of 1 unit from existing slots should be accepted (no touching)."""
    timeline = [(1, 4)]
    success, result = plan_upgrade_slot(timeline, (6, 9))
    assert success is True
    assert (6, 9) in result
    assert len(result) == 2


def test_adjacent_touching_with_float_boundaries():
    """Adjacent slots with float boundaries where end of new window equals start of existing should conflict."""
    timeline = [(5.0, 10.0)]
    success, result = plan_upgrade_slot(timeline, (2.0, 5.0))
    assert success is False
    assert result == [(5.0, 10.0)]