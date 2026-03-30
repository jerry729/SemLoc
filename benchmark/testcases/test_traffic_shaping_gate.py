import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.traffic_shaping_gate import traffic_shaping_gate
else:
    from programs.traffic_shaping_gate import traffic_shaping_gate


def test_no_prior_requests_allows_traffic():
    """A client with no recorded requests should be admitted immediately."""
    allowed, remaining = traffic_shaping_gate([], now=100)
    assert allowed is True
    assert remaining == 5


def test_few_requests_well_under_limit():
    """When the client has only two active requests the gate should stay open."""
    timestamps = [95.0, 97.0]
    allowed, remaining = traffic_shaping_gate(timestamps, now=100)
    assert allowed is True
    assert remaining == 3


def test_old_timestamps_outside_window_are_ignored():
    """Requests older than the window should not count toward the limit."""
    timestamps = [80.0, 82.0, 85.0]
    allowed, remaining = traffic_shaping_gate(timestamps, now=100)
    assert allowed is True
    assert remaining == 5


def test_clearly_over_limit_denies_traffic():
    """When the active count exceeds the limit the gate must deny entry."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0]
    allowed, remaining = traffic_shaping_gate(timestamps, now=100, limit=5)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_denies_traffic():
    """When active requests equal the limit, no more should be admitted."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = traffic_shaping_gate(timestamps, now=100, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_one_more():
    """With one slot remaining the gate should allow exactly one more request."""
    timestamps = [91.0, 92.0, 93.0, 94.0]
    allowed, remaining = traffic_shaping_gate(timestamps, now=100, limit=5)
    assert allowed is True
    assert remaining == 1


def test_custom_window_and_limit():
    """Custom window and limit parameters should be respected."""
    timestamps = [48.0, 49.0, 50.0]
    allowed, remaining = traffic_shaping_gate(
        timestamps, now=50, window=5, limit=3
    )
    assert allowed is False
    assert remaining == 0


def test_single_request_at_limit_boundary():
    """A single active request at a limit of 1 must be denied."""
    timestamps = [99.0]
    allowed, remaining = traffic_shaping_gate(
        timestamps, now=100, window=10, limit=1
    )
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises():
    """A window below the minimum should raise a ValueError."""
    with pytest.raises(ValueError):
        traffic_shaping_gate([], now=100, window=0)


def test_invalid_limit_raises():
    """A limit below the minimum should raise a ValueError."""
    with pytest.raises(ValueError):
        traffic_shaping_gate([], now=100, limit=0)
