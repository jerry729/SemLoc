import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.inspection_booking import inspection_booking
else:
    from programs.inspection_booking import inspection_booking


# --- Tests that FAIL on buggy, PASS on correct (adjacent endpoint overlap) ---

def test_candidate_end_equals_existing_start():
    """Adjacent windows sharing an endpoint should be considered overlapping."""
    existing = [(100, 130)]
    candidate = (70, 100)  # candidate end == existing start
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is False
    assert schedule == [(100, 130)]


def test_candidate_start_equals_existing_end():
    """A candidate whose start equals an existing slot's end should overlap."""
    existing = [(50, 80)]
    candidate = (80, 120)  # candidate start == existing end
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is False
    assert schedule == [(50, 80)]


def test_adjacent_at_shared_boundary_multiple_existing():
    """When multiple slots exist, adjacency at a shared boundary should conflict."""
    existing = [(0, 30), (60, 90)]
    candidate = (30, 60)  # candidate start == first end, candidate end == second start
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is False
    assert schedule == [(0, 30), (60, 90)]


def test_candidate_exactly_touches_existing_end_large_values():
    """Adjacent windows with large time values sharing an endpoint should overlap."""
    existing = [(1000, 1200)]
    candidate = (1200, 1400)  # candidate start == existing end
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is False
    assert schedule == [(1000, 1200)]


# --- Tests that PASS on BOTH versions (baseline behavior) ---

def test_no_overlap_with_gap():
    """Non-overlapping windows with a gap between them should be accepted."""
    existing = [(100, 130)]
    candidate = (150, 180)
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is True
    assert candidate in schedule


def test_clear_overlap_rejected():
    """A candidate that clearly overlaps an existing slot should be rejected."""
    existing = [(100, 200)]
    candidate = (150, 250)
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is False
    assert schedule == [(100, 200)]


def test_empty_schedule_accepts_candidate():
    """A candidate should always be accepted into an empty schedule."""
    existing = []
    candidate = (0, 30)
    accepted, schedule = inspection_booking(existing, candidate)
    assert accepted is True
    assert schedule == [(0, 30)]


def test_invalid_candidate_raises_value_error():
    """A candidate with start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        inspection_booking([], (100, 50))