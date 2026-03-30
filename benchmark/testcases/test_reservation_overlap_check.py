import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.reservation_overlap_check import reservation_overlap_check
else:
    from programs.reservation_overlap_check import reservation_overlap_check


def test_no_existing_reservations():
    """A candidate against an empty schedule should never conflict."""
    assert reservation_overlap_check([], (10, 20)) is False


def test_clearly_disjoint_reservations():
    """Non-overlapping intervals that are far apart produce no conflict."""
    existing = [(1, 5), (30, 40)]
    assert reservation_overlap_check(existing, (10, 20)) is False


def test_full_containment_detected():
    """A candidate fully inside an existing booking must be flagged."""
    existing = [(5, 50)]
    assert reservation_overlap_check(existing, (10, 20)) is True


def test_partial_overlap_at_start():
    """A candidate that starts before and ends during an existing booking overlaps."""
    existing = [(15, 25)]
    assert reservation_overlap_check(existing, (10, 20)) is True


def test_invalid_candidate_raises():
    """Degenerate intervals where start >= end must be rejected."""
    with pytest.raises(ValueError):
        reservation_overlap_check([(1, 5)], (20, 10))


def test_candidate_ends_at_existing_start_shared_endpoint():
    """When the candidate's end equals an existing reservation's start, the
    shared endpoint means the resource is double-booked at that instant."""
    existing = [(20, 30)]
    assert reservation_overlap_check(existing, (10, 20)) is True


def test_candidate_starts_at_existing_end_shared_endpoint():
    """When the candidate begins exactly where an existing reservation ends,
    the resource is still occupied at that boundary moment."""
    existing = [(5, 10)]
    assert reservation_overlap_check(existing, (10, 20)) is True


def test_adjacent_but_no_shared_endpoint():
    """Intervals [5,9] and [10,20] share no point and must not conflict."""
    existing = [(5, 9)]
    assert reservation_overlap_check(existing, (10, 20)) is False


def test_multiple_bookings_one_boundary_touch():
    """Among several bookings, a single boundary-touch should still be detected."""
    existing = [(1, 3), (5, 10), (25, 30)]
    assert reservation_overlap_check(existing, (10, 20)) is True


def test_identical_reservation():
    """A candidate identical to an existing booking is clearly a conflict."""
    existing = [(10, 20)]
    assert reservation_overlap_check(existing, (10, 20)) is True
