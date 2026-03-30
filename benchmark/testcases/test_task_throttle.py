import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.task_throttle import task_throttle
else:
    from programs.task_throttle import task_throttle


def test_no_prior_events_allows_task():
    """With no previous tasks, the throttle should allow execution and report full remaining capacity."""
    allowed, remaining = task_throttle([], 10.0)
    assert allowed is True
    assert remaining == 3


def test_single_event_within_window():
    """One prior event within the window should leave two remaining slots."""
    allowed, remaining = task_throttle([8.0], 10.0)
    assert allowed is True
    assert remaining == 2


def test_events_outside_window_are_ignored():
    """Events that fall before the sliding window should not count toward the limit."""
    allowed, remaining = task_throttle([1.0, 2.0, 3.0], 10.0)
    assert allowed is True
    assert remaining == 3


def test_mixed_inside_and_outside_window():
    """Only events within the window should be counted; older events are irrelevant."""
    allowed, remaining = task_throttle([1.0, 2.0, 7.0, 9.0], 10.0)
    assert allowed is True
    assert remaining == 1


def test_custom_window_and_limit_under_capacity():
    """A custom window and limit should be respected when under capacity."""
    allowed, remaining = task_throttle([95.0, 96.0], 100.0, window=10, limit=5)
    assert allowed is True
    assert remaining == 3


def test_exactly_at_limit_denies_task():
    """When the number of recent events exactly equals the limit, no further tasks should be allowed."""
    allowed, remaining = task_throttle([6.0, 7.0, 8.0], 10.0, limit=3)
    assert allowed is False
    assert remaining == 0


def test_at_limit_with_custom_parameters():
    """A rate limiter configured with custom window and limit must deny at exactly the threshold."""
    timestamps = [91.0, 93.0, 95.0, 97.0, 99.0]
    allowed, remaining = task_throttle(timestamps, 100.0, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_exceeding_limit_denies_task():
    """When recent events exceed the limit, the task must be denied."""
    allowed, remaining = task_throttle([6.0, 7.0, 8.0, 9.0], 10.0, limit=3)
    assert allowed is False
    assert remaining == 0


def test_boundary_event_on_window_edge_is_included():
    """An event whose timestamp equals the window start boundary should count as recent."""
    allowed, remaining = task_throttle([5.0, 7.0, 9.0], 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """Window size below the minimum threshold should raise a ValueError."""
    with pytest.raises(ValueError):
        task_throttle([1.0], 10.0, window=0)
