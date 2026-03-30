import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.reserve_lane import reserve_lane
else:
    from programs.reserve_lane import reserve_lane


# --- Tests that PASS on both versions (baseline behavior) ---

def test_empty_schedule_accepts_candidate():
    """A candidate should be accepted when the schedule is empty."""
    accepted, schedule = reserve_lane([], (3, 7))
    assert accepted is True
    assert schedule == [(3, 7)]


def test_non_overlapping_candidates_accepted():
    """Candidates that are clearly separated from existing slots should be accepted."""
    accepted, schedule = reserve_lane([(1, 3)], (5, 8))
    assert accepted is True
    assert schedule == [(1, 3), (5, 8)]


def test_fully_overlapping_candidate_rejected():
    """A candidate that fully overlaps an existing slot should be rejected."""
    accepted, schedule = reserve_lane([(2, 6)], (3, 5))
    assert accepted is False
    assert schedule == [(2, 6)]


def test_invalid_candidate_raises_value_error():
    """A candidate where start >= end should raise ValueError."""
    with pytest.raises(ValueError):
        reserve_lane([], (5, 3))


# --- Tests that FAIL on buggy version, PASS on correct version ---

def test_candidate_end_touches_existing_start():
    """A candidate whose end equals an existing slot's start should be detected as overlapping."""
    # candidate (1, 5) touches existing (5, 10) at boundary 5
    accepted, schedule = reserve_lane([(5, 10)], (1, 5))
    assert accepted is False
    assert schedule == [(5, 10)]


def test_candidate_start_touches_existing_end():
    """A candidate whose start equals an existing slot's end should be detected as overlapping."""
    # candidate (5, 8) touches existing (2, 5) at boundary 5
    accepted, schedule = reserve_lane([(2, 5)], (5, 8))
    assert accepted is False
    assert schedule == [(2, 5)]


def test_adjacent_slots_conflict_symmetry():
    """Two adjacent windows touching at a single point should conflict regardless of order."""
    # existing (10, 20), candidate starts exactly at 20
    accepted, schedule = reserve_lane([(10, 20)], (20, 30))
    assert accepted is False
    assert schedule == [(10, 20)]


def test_multiple_existing_boundary_touch():
    """A candidate touching the boundary of any one existing slot should be rejected."""
    existing = [(0, 5), (10, 15), (20, 25)]
    # candidate (15, 20) touches existing (10, 15) at 15 and existing (20, 25) at 20
    accepted, schedule = reserve_lane(existing, (15, 20))
    assert accepted is False
    assert schedule == existing


def test_candidate_end_equals_existing_start_unit_interval():
    """A unit-length candidate ending exactly at an existing slot's start should conflict."""
    accepted, schedule = reserve_lane([(3, 6)], (2, 3))
    assert accepted is False
    assert schedule == [(3, 6)]


def test_candidate_start_equals_existing_end_unit_interval():
    """A unit-length candidate starting exactly at an existing slot's end should conflict."""
    accepted, schedule = reserve_lane([(1, 4)], (4, 5))
    assert accepted is False
    assert schedule == [(1, 4)]