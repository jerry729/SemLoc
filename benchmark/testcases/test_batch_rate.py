import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.batch_rate import batch_rate
else:
    from programs.batch_rate import batch_rate


NOW = 1_700_000_000.0


def test_no_prior_activity_allows_full_quota():
    """An empty history should grant the entire rate-limit budget."""
    allowed, remaining = batch_rate([], NOW, window=60, limit=20)
    assert allowed is True
    assert remaining == 20


def test_well_below_limit_allows_request():
    """When recent activity is comfortably below the cap, requests should be allowed."""
    timestamps = [NOW - 10, NOW - 20, NOW - 30]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=20)
    assert allowed is True
    assert remaining == 17


def test_old_timestamps_outside_window_are_ignored():
    """Events older than the window must not count toward the rate limit."""
    timestamps = [NOW - 120, NOW - 200, NOW - 300]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_clearly_over_limit_is_rejected():
    """When recent activity significantly exceeds the cap, the request must be denied."""
    timestamps = [NOW - i for i in range(25)]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=20)
    assert allowed is False
    assert remaining == 0


def test_custom_window_duration():
    """The sliding window parameter should correctly shift the cutoff boundary."""
    timestamps = [NOW - 50, NOW - 80]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=5)
    assert allowed is True
    assert remaining == 4


def test_exactly_at_limit_should_deny():
    """When recent events equal the limit exactly, no further requests should be allowed."""
    timestamps = [NOW - i for i in range(20)]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=20)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_should_allow_one_remaining():
    """When recent count is one fewer than the limit, exactly one request should be available."""
    timestamps = [NOW - i for i in range(19)]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=20)
    assert allowed is True
    assert remaining == 1


def test_limit_of_one_with_one_recent_event():
    """A rate limit of 1 with one recent event should deny further activity."""
    timestamps = [NOW - 5]
    allowed, remaining = batch_rate(timestamps, NOW, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_limit_of_one_with_no_recent_events():
    """A rate limit of 1 with no recent history should allow exactly one request."""
    allowed, remaining = batch_rate([], NOW, window=60, limit=1)
    assert allowed is True
    assert remaining == 1


def test_invalid_future_timestamp_raises():
    """Timestamps that lie in the future relative to 'now' are invalid and must be rejected."""
    with pytest.raises(ValueError):
        batch_rate([NOW + 100], NOW, window=60, limit=20)
