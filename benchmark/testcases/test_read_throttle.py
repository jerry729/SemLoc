import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.read_throttle import read_throttle
else:
    from programs.read_throttle import read_throttle


def test_no_prior_reads_allows_action():
    """With an empty history the throttle should allow reads up to the limit."""
    allowed, remaining = read_throttle([], now=100.0)
    assert allowed is True
    assert remaining == 5


def test_few_reads_within_window():
    """When usage is well below the limit, reads should be permitted."""
    timestamps = [95.0, 96.0, 97.0]
    allowed, remaining = read_throttle(timestamps, now=100.0)
    assert allowed is True
    assert remaining == 2


def test_reads_outside_window_are_ignored():
    """Timestamps older than the sliding window must not count."""
    timestamps = [80.0, 81.0, 82.0]
    allowed, remaining = read_throttle(timestamps, now=100.0)
    assert allowed is True
    assert remaining == 5


def test_mixed_old_and_recent_reads():
    """Only recent timestamps should influence the remaining count."""
    timestamps = [80.0, 85.0, 91.0, 95.0, 99.0]
    allowed, remaining = read_throttle(timestamps, now=100.0)
    assert allowed is True
    assert remaining == 2


def test_exactly_at_limit_denies_further_reads():
    """When the number of active reads equals the limit, no more reads are allowed."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = read_throttle(timestamps, now=100.0, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_still_permits():
    """With exactly limit-1 active reads, one more should be allowed."""
    timestamps = [92.0, 93.0, 94.0, 95.0]
    allowed, remaining = read_throttle(timestamps, now=100.0, window=10, limit=5)
    assert allowed is True
    assert remaining == 1


def test_custom_window_and_limit_at_boundary():
    """Custom parameters at the exact boundary should deny the request."""
    timestamps = [48.0, 49.0, 50.0]
    allowed, remaining = read_throttle(timestamps, now=50.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_exceeding_limit_returns_zero_remaining():
    """When active reads exceed the limit, remaining must be zero."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = read_throttle(timestamps, now=100.0, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_value_error():
    """A window smaller than the minimum must raise ValueError."""
    with pytest.raises(ValueError):
        read_throttle([], now=100.0, window=0)


def test_limit_equals_one_at_boundary():
    """With a limit of 1 and exactly 1 active read, access should be denied."""
    timestamps = [99.0]
    allowed, remaining = read_throttle(timestamps, now=100.0, window=10, limit=1)
    assert allowed is False
    assert remaining == 0
