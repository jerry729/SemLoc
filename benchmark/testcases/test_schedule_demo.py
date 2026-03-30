import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_demo import schedule_demo
else:
    from programs.schedule_demo import schedule_demo


def test_schedule_into_empty_calendar():
    """A demo should always be accepted when the calendar is empty."""
    accepted, updated = schedule_demo([], (9, 10))
    assert accepted is True
    assert updated == [(9, 10)]


def test_non_overlapping_before_existing():
    """An interval ending before the first slot should be accepted."""
    accepted, updated = schedule_demo([(10, 12)], (5, 8))
    assert accepted is True
    assert updated == [(5, 8), (10, 12)]


def test_non_overlapping_after_existing():
    """An interval starting well after the last slot should be accepted."""
    accepted, updated = schedule_demo([(10, 12)], (15, 18))
    assert accepted is True
    assert updated == [(10, 12), (15, 18)]


def test_fully_overlapping_interval_rejected():
    """An interval that fully contains an existing slot must be rejected."""
    accepted, updated = schedule_demo([(10, 12)], (8, 14))
    assert accepted is False
    assert updated == [(10, 12)]


def test_invalid_degenerate_interval_raises():
    """A zero-duration or inverted interval is invalid and must raise."""
    with pytest.raises(ValueError):
        schedule_demo([], (10, 10))
    with pytest.raises(ValueError):
        schedule_demo([], (12, 8))


def test_adjacent_interval_end_touches_start():
    """An interval whose end equals the start of an existing slot represents
    adjacent booking and must be rejected as overlapping at the boundary."""
    accepted, _ = schedule_demo([(10, 12)], (8, 10))
    assert accepted is False


def test_adjacent_interval_start_touches_end():
    """An interval whose start equals the end of an existing slot represents
    adjacent booking and must be rejected as overlapping at the boundary."""
    accepted, _ = schedule_demo([(10, 12)], (12, 14))
    assert accepted is False


def test_exact_duplicate_slot_rejected():
    """Booking the exact same time slot again must be rejected."""
    accepted, _ = schedule_demo([(10, 12)], (10, 12))
    assert accepted is False


def test_multiple_slots_interleaved_acceptance():
    """A gap between two existing slots should allow a fitting demo."""
    existing = [(2, 4), (8, 10), (14, 16)]
    accepted, updated = schedule_demo(existing, (5, 7))
    assert accepted is True
    assert (5, 7) in updated
    assert updated == sorted(updated)


def test_touching_both_neighbors_rejected():
    """An interval that exactly fills the gap between two slots touches both
    neighbors and must be rejected."""
    existing = [(2, 5), (10, 14)]
    accepted, _ = schedule_demo(existing, (5, 10))
    assert accepted is False
