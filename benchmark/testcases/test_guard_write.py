import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.guard_write import guard_write
else:
    from programs.guard_write import guard_write


def test_no_prior_writes_allows_request():
    """An empty history should always permit the write and report full remaining capacity."""
    allowed, remaining = guard_write([], 100.0)
    assert allowed is True
    assert remaining == 3


def test_single_recent_event_allows_request():
    """With only one write in the window, the request should be permitted."""
    allowed, remaining = guard_write([98.0], 100.0)
    assert allowed is True
    assert remaining == 2


def test_old_events_outside_window_are_ignored():
    """Timestamps older than the sliding window should not count against the limit."""
    allowed, remaining = guard_write([90.0, 91.0, 92.0, 93.0], 100.0)
    assert allowed is True
    assert remaining == 3


def test_events_exceeding_limit_denied():
    """When more events than the limit exist in the window, the write must be denied."""
    allowed, remaining = guard_write([96.0, 97.0, 98.0, 99.0], 100.0)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_denies_request():
    """When the number of recent events equals the limit, no further writes should be allowed."""
    allowed, remaining = guard_write([96.0, 97.0, 98.0], 100.0)
    assert allowed is False
    assert remaining == 0


def test_custom_window_and_limit():
    """Custom window and limit parameters should be respected correctly."""
    allowed, remaining = guard_write([8.0, 9.0], 10.0, window=3, limit=2)
    assert allowed is False
    assert remaining == 0


def test_custom_limit_permits_when_below():
    """With a higher custom limit, the same history should be permitted."""
    allowed, remaining = guard_write([96.0, 97.0, 98.0], 100.0, limit=5)
    assert allowed is True
    assert remaining == 2


def test_boundary_event_at_window_edge_included():
    """A timestamp exactly at the window boundary should be counted as recent."""
    allowed, remaining = guard_write([95.0, 96.0, 97.0], 100.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """A window smaller than the minimum must raise ValueError."""
    with pytest.raises(ValueError):
        guard_write([], 100.0, window=0)


def test_invalid_limit_raises_error():
    """A limit of zero must raise ValueError since at least one write must be configurable."""
    with pytest.raises(ValueError):
        guard_write([], 100.0, limit=0)
