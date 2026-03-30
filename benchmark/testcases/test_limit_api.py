import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_api import limit_api
else:
    from programs.limit_api import limit_api


def test_no_previous_requests():
    """A caller with no history should be fully allowed with the entire quota remaining."""
    allowed, remaining = limit_api([], 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_well_under_limit():
    """A caller with a few requests well below the cap should be allowed."""
    ts = [990.0, 995.0]
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=10)
    assert allowed is True
    assert remaining == 8


def test_old_timestamps_outside_window():
    """Requests that occurred before the sliding window should not count."""
    ts = [100.0, 200.0, 300.0]
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=3)
    assert allowed is True
    assert remaining == 3


def test_exceeds_limit_clearly():
    """When recent activity clearly exceeds the limit, the request must be denied."""
    ts = [999.0] * 10
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit():
    """A caller with one slot remaining should still be allowed."""
    ts = [990.0 + i for i in range(4)]
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 1


def test_exactly_at_limit():
    """When the number of recent requests equals the limit, the caller has exhausted quota."""
    ts = [990.0 + i for i in range(5)]
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_at_limit_with_default_params():
    """With default window and limit, exactly 20 recent requests should exhaust capacity."""
    ts = [950.0 + i for i in range(20)]
    allowed, remaining = limit_api(ts, 1000.0)
    assert allowed is False
    assert remaining == 0


def test_boundary_timestamp_equals_cutoff():
    """A timestamp exactly at the cutoff edge should be counted as recent."""
    ts = [940.0]
    allowed, remaining = limit_api(ts, 1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises():
    """A window smaller than the minimum should raise a ValueError."""
    with pytest.raises(ValueError):
        limit_api([], 1000.0, window=0, limit=5)


def test_mixed_old_and_recent_at_limit():
    """Only timestamps within the window should contribute; reaching the exact limit denies access."""
    old = [800.0, 850.0]
    recent = [960.0 + i for i in range(3)]
    allowed, remaining = limit_api(old + recent, 1000.0, window=60, limit=3)
    assert allowed is False
    assert remaining == 0
