import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.downtime_booking import downtime_booking
else:
    from programs.downtime_booking import downtime_booking


def test_empty_schedule_accepts_any_valid_window():
    """A valid candidate should always be accepted when the schedule is empty."""
    accepted, schedule = downtime_booking([], (100, 200))
    assert accepted is True
    assert schedule == [(100, 200)]


def test_non_overlapping_windows_accepted():
    """Two windows with a gap between them should both be in the schedule."""
    accepted, schedule = downtime_booking([(100, 200)], (300, 400))
    assert accepted is True
    assert (100, 200) in schedule
    assert (300, 400) in schedule


def test_fully_overlapping_window_rejected():
    """A candidate that falls entirely within an existing window must be rejected."""
    accepted, schedule = downtime_booking([(100, 400)], (150, 350))
    assert accepted is False
    assert schedule == [(100, 400)]


def test_partial_overlap_rejected():
    """A candidate that partially overlaps an existing window must be rejected."""
    accepted, schedule = downtime_booking([(100, 300)], (200, 400))
    assert accepted is False
    assert schedule == [(100, 300)]


def test_invalid_window_raises_value_error():
    """A window where start >= end is invalid and should raise ValueError."""
    with pytest.raises(ValueError):
        downtime_booking([], (500, 500))
    with pytest.raises(ValueError):
        downtime_booking([], (600, 400))


def test_adjacent_window_end_equals_start_rejected():
    """When a candidate starts exactly where an existing window ends, they share a boundary and should be treated as overlapping."""
    accepted, schedule = downtime_booking([(100, 200)], (200, 300))
    assert accepted is False
    assert schedule == [(100, 200)]


def test_adjacent_window_start_equals_end_rejected():
    """When a candidate ends exactly where an existing window starts, they share a boundary and should be treated as overlapping."""
    accepted, schedule = downtime_booking([(200, 300)], (100, 200))
    assert accepted is False
    assert schedule == [(200, 300)]


def test_schedule_returned_sorted():
    """The returned schedule must always be sorted by window start time."""
    accepted, schedule = downtime_booking([(300, 400), (100, 150)], (500, 600))
    assert accepted is True
    starts = [w[0] for w in schedule]
    assert starts == sorted(starts)


def test_multiple_existing_windows_with_exact_boundary_touch():
    """A candidate that touches boundaries of two different existing windows should be rejected for both."""
    existing = [(100, 200), (300, 400)]
    accepted, schedule = downtime_booking(existing, (200, 300))
    assert accepted is False
    assert sorted(schedule) == sorted(existing)


def test_candidate_before_all_existing_no_overlap():
    """A candidate placed well before all existing windows should be accepted."""
    accepted, schedule = downtime_booking([(500, 600), (700, 800)], (50, 100))
    assert accepted is True
    assert len(schedule) == 3
    assert schedule[0] == (50, 100)
