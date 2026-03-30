import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_delivery_slot import plan_delivery_slot
else:
    from programs.plan_delivery_slot import plan_delivery_slot


# ============================================================
# Tests that PASS on BOTH versions (baseline behavior)
# ============================================================

def test_empty_timeline_accepts_any_valid_window():
    """A valid window should always be placed into an empty timeline."""
    success, result = plan_delivery_slot([], (1, 5))
    assert success is True
    assert result == [(1, 5)]


def test_non_overlapping_window_placed_correctly():
    """A window that is clearly separated from existing slots should be accepted."""
    timeline = [(1, 3), (7, 10)]
    success, result = plan_delivery_slot(timeline, (4, 6))
    assert success is True
    assert (4, 6) in result
    assert len(result) == 3


def test_fully_overlapping_window_rejected():
    """A window that fully overlaps an existing slot should be rejected."""
    timeline = [(5, 10)]
    success, result = plan_delivery_slot(timeline, (6, 8))
    assert success is False
    assert result is timeline


def test_invalid_window_raises_value_error():
    """A window with start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        plan_delivery_slot([], (5, 3))


# ============================================================
# Tests that PASS on CORRECT but FAIL on BUGGY
# These target the exact boundary: touching endpoints (a == e or b == s)
# ============================================================

def test_window_touching_end_of_existing_slot():
    """A new window whose start equals the end of an existing slot should be accepted (adjacent, no overlap)."""
    # Existing slot ends at 5, new window starts at 5
    # Correct: a > e is False (5 > 5 is False) but b < s check handles it... 
    # Actually: existing (2,5), new window (5,8): a=5, e=5 → a > e is False in correct, a >= e is True in buggy
    # Correct: not (b < s or a > e) = not (8 < 2 or 5 > 5) = not (False or False) = True → conflict detected? No...
    # Wait, let me re-read. Correct version: `not (b < s or a > e)` means overlap if True.
    # For (2,5) and window (5,8): not (8 < 2 or 5 > 5) = not (False or False) = not False = True → overlap → rejected
    # Buggy: not (b <= s or a >= e) = not (8 <= 2 or 5 >= 5) = not (False or True) = not True = False → no overlap → accepted
    # So buggy ACCEPTS touching windows, correct REJECTS them.
    # Hmm, but which behavior is actually "correct"? The diff says correct uses strict comparison.
    # In correct version: touching endpoints ARE considered overlapping (stricter).
    # So the test should expect REJECTION for touching endpoints.
    timeline = [(2, 5)]
    success, result = plan_delivery_slot(timeline, (5, 8))
    assert success is False
    assert result is timeline


def test_window_touching_start_of_existing_slot():
    """A new window whose end equals the start of an existing slot should be rejected as overlapping."""
    # Existing (5, 10), new window (2, 5): a=2, b=5, s=5, e=10
    # Correct: not (5 < 5 or 2 > 10) = not (False or False) = True → overlap → rejected
    # Buggy: not (5 <= 5 or 2 >= 10) = not (True or False) = False → no overlap → accepted
    timeline = [(5, 10)]
    success, result = plan_delivery_slot(timeline, (2, 5))
    assert success is False
    assert result is timeline


def test_window_touching_both_adjacent_slots():
    """A window that touches both the end of one slot and the start of another should be rejected."""
    # Existing [(1,3), (7,10)], new window (3, 7)
    # For (1,3): Correct: not (7 < 1 or 3 > 3) = not (False or False) = True → overlap
    # Buggy: not (7 <= 1 or 3 >= 3) = not (False or True) = False → no overlap
    # For (7,10): Correct: not (7 < 7 or 3 > 10) = not (False or False) = True → overlap
    # Buggy: not (7 <= 7 or 3 >= 10) = not (True or False) = False → no overlap
    # Buggy accepts, correct rejects
    timeline = [(1, 3), (7, 10)]
    success, result = plan_delivery_slot(timeline, (3, 7))
    assert success is False
    assert result is timeline


def test_window_touching_single_endpoint_among_multiple_slots():
    """A window touching exactly one existing slot's endpoint among several should be rejected."""
    timeline = [(0, 2), (10, 15), (20, 25)]
    # New window (15, 18): a=15, b=18
    # Check (10,15): Correct: not (18 < 10 or 15 > 15) = not (False or False) = True → overlap
    # Buggy: not (18 <= 10 or 15 >= 15) = not (False or True) = False → no overlap
    success, result = plan_delivery_slot(timeline, (15, 18))
    assert success is False
    assert result is timeline


def test_non_touching_gap_still_accepted():
    """A window with a clear gap (no touching) between existing slots should be accepted by both versions."""
    # This confirms that slightly separated windows are fine in both versions
    timeline = [(1, 3), (7, 10)]
    success, result = plan_delivery_slot(timeline, (4, 6))
    assert success is True
    assert len(result) == 3
    assert (4, 6) in result