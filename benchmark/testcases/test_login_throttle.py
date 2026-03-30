import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.login_throttle import login_throttle
else:
    from programs.login_throttle import login_throttle


def test_no_prior_attempts_allows_login():
    """A user with no recent login history should be allowed to log in."""
    allowed, remaining = login_throttle([], 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_few_attempts_well_under_limit():
    """A handful of attempts far below the cap should be permitted."""
    timestamps = [990.0, 991.0, 992.0]
    allowed, remaining = login_throttle(timestamps, 1000.0, window=60, limit=10)
    assert allowed is True
    assert remaining == 7


def test_old_attempts_outside_window_ignored():
    """Attempts older than the sliding window must not count toward the limit."""
    timestamps = [100.0, 200.0, 300.0]
    allowed, remaining = login_throttle(timestamps, 1000.0, window=60, limit=3)
    assert allowed is True
    assert remaining == 3


def test_exceeding_limit_denies_login():
    """When attempts clearly exceed the limit, access should be denied."""
    timestamps = [950.0 + i for i in range(8)]
    allowed, remaining = login_throttle(timestamps, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_denies_login():
    """When the number of recent attempts equals the limit, access must be denied."""
    timestamps = [950.0 + i for i in range(5)]
    allowed, remaining = login_throttle(timestamps, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_login():
    """One fewer attempt than the limit should still allow login."""
    timestamps = [950.0 + i for i in range(4)]
    allowed, remaining = login_throttle(timestamps, 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 1


def test_limit_of_one_with_one_recent_attempt():
    """A strict limit of 1 must deny when exactly 1 recent attempt exists."""
    allowed, remaining = login_throttle([999.0], 1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_limit_of_one_with_no_recent_attempts():
    """A strict limit of 1 should allow login when no recent attempts exist."""
    allowed, remaining = login_throttle([], 1000.0, window=60, limit=1)
    assert allowed is True
    assert remaining == 1


def test_mixed_old_and_recent_timestamps():
    """Only timestamps inside the window should be counted toward the cap."""
    old = [800.0, 850.0, 900.0]
    recent = [960.0, 970.0, 980.0]
    allowed, remaining = login_throttle(old + recent, 1000.0, window=60, limit=3)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """A non-positive window duration must raise a ValueError."""
    with pytest.raises(ValueError):
        login_throttle([], 1000.0, window=0, limit=5)
