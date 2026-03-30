import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.guard_search import guard_search
else:
    from programs.guard_search import guard_search


def test_no_previous_requests_allows_search():
    """A user with no recent search history should be fully allowed."""
    allowed, remaining = guard_search([], 100.0)
    assert allowed is True
    assert remaining == 5


def test_few_requests_below_limit_allows_search():
    """When the number of recent requests is well below the limit, access is granted."""
    timestamps = [95.0, 96.0]
    allowed, remaining = guard_search(timestamps, 100.0)
    assert allowed is True
    assert remaining == 3


def test_old_timestamps_outside_window_are_ignored():
    """Requests older than the sliding window should not count toward the limit."""
    timestamps = [80.0, 85.0, 89.9]
    allowed, remaining = guard_search(timestamps, 100.0)
    assert allowed is True
    assert remaining == 5


def test_requests_clearly_over_limit_are_blocked():
    """When the user has exceeded the limit by a wide margin, access is denied."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0, 97.0]
    allowed, remaining = guard_search(timestamps, 100.0)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_denies_new_search():
    """When the user has exactly used up the allowed quota, no further searches are permitted."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = guard_search(timestamps, 100.0, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_exactly_one_more():
    """A user one request shy of the limit should be allowed with exactly 1 remaining."""
    timestamps = [92.0, 93.0, 94.0, 95.0]
    allowed, remaining = guard_search(timestamps, 100.0, window=10, limit=5)
    assert allowed is True
    assert remaining == 1


def test_custom_window_and_limit_at_boundary():
    """Custom rate-limit parameters should be respected at the boundary."""
    timestamps = [98.0, 99.0, 100.0]
    allowed, remaining = guard_search(timestamps, 100.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_custom_limit_exactly_met_denies():
    """When a custom limit is exactly reached, the guard should deny further access."""
    timestamps = [99.0, 100.0]
    allowed, remaining = guard_search(timestamps, 100.0, window=5, limit=2)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """A window smaller than the minimum threshold should raise a ValueError."""
    with pytest.raises(ValueError):
        guard_search([], 100.0, window=0)


def test_mixed_old_and_recent_timestamps():
    """Only recent timestamps within the window affect the remaining count."""
    timestamps = [50.0, 60.0, 70.0, 92.0, 95.0, 98.0]
    allowed, remaining = guard_search(timestamps, 100.0, window=10, limit=5)
    assert allowed is True
    assert remaining == 2
