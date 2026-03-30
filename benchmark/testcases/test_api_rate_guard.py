import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.api_rate_guard import api_rate_guard
else:
    from programs.api_rate_guard import api_rate_guard


def test_no_prior_requests_allows_call():
    """With no request history, the full quota should be available."""
    allowed, remaining = api_rate_guard([], 1000.0, window=60, limit=10)
    assert allowed is True
    assert remaining == 10


def test_well_under_limit_returns_correct_remaining():
    """When usage is well below the cap, remaining slots are reported accurately."""
    ts = [990.0, 995.0, 998.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=10)
    assert allowed is True
    assert remaining == 7


def test_old_timestamps_outside_window_are_ignored():
    """Requests older than the sliding window must not count toward the limit."""
    ts = [900.0, 910.0, 920.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_over_limit_denies_request():
    """When the number of recent requests clearly exceeds the limit, access is denied."""
    ts = [float(t) for t in range(950, 965)]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_value_error():
    """A zero-length window violates minimum configuration constraints."""
    with pytest.raises(ValueError):
        api_rate_guard([], 1000.0, window=0, limit=10)


def test_exactly_at_limit_denies_request():
    """When the count of recent requests equals the limit, no further calls are allowed."""
    ts = [991.0, 992.0, 993.0, 994.0, 995.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_still_allows():
    """With exactly one slot remaining, the call should be permitted."""
    ts = [991.0, 992.0, 993.0, 994.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 1


def test_limit_of_one_with_one_recent_request():
    """A rate limit of 1 must deny when exactly 1 request is in the window."""
    ts = [999.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_boundary_timestamp_included_in_window():
    """A timestamp exactly at the cutoff edge is within the window."""
    ts = [940.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_custom_large_window_accumulates_all():
    """A very large window should capture all historical requests."""
    ts = [100.0, 200.0, 300.0, 400.0, 500.0]
    allowed, remaining = api_rate_guard(ts, 1000.0, window=1000, limit=5)
    assert allowed is False
    assert remaining == 0
