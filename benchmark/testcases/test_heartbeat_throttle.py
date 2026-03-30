import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.heartbeat_throttle import heartbeat_throttle
else:
    from programs.heartbeat_throttle import heartbeat_throttle


def test_no_prior_heartbeats():
    """With no prior heartbeats the action should always be allowed with full remaining capacity."""
    allowed, remaining = heartbeat_throttle([], 100.0)
    assert allowed is True
    assert remaining == 5


def test_well_below_limit():
    """When the number of active heartbeats is well below the limit, the action is permitted."""
    timestamps = [95.0, 96.0]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0)
    assert allowed is True
    assert remaining == 3


def test_expired_timestamps_ignored():
    """Timestamps outside the sliding window should not count toward the rate limit."""
    timestamps = [80.0, 85.0, 89.9]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0)
    assert allowed is True
    assert remaining == 5


def test_mixed_expired_and_active():
    """Only timestamps within the window contribute to the count."""
    timestamps = [80.0, 85.0, 91.0, 95.0, 99.0]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0)
    assert allowed is True
    assert remaining == 2


def test_custom_window_and_limit():
    """Custom window and limit parameters should be respected."""
    timestamps = [48.0, 49.0]
    allowed, remaining = heartbeat_throttle(timestamps, 50.0, window=5, limit=3)
    assert allowed is True
    assert remaining == 1


def test_throttle_when_exceeding_limit():
    """When active heartbeats clearly exceed the limit the action must be denied."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_throttle_at_exact_limit():
    """When the active count equals the limit, the next heartbeat must be denied."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_at_exact_limit_with_custom_params():
    """Reaching the exact limit with custom parameters should deny the action."""
    timestamps = [8.0, 9.0, 10.0]
    allowed, remaining = heartbeat_throttle(timestamps, 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_single_heartbeat_at_limit_one():
    """With a limit of 1 and one active heartbeat, the action should be denied."""
    timestamps = [99.0]
    allowed, remaining = heartbeat_throttle(timestamps, 100.0, limit=1)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises():
    """A window below the minimum must raise ValueError."""
    with pytest.raises(ValueError):
        heartbeat_throttle([], 100.0, window=0)
