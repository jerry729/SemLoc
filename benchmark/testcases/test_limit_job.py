import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_job import limit_job
else:
    from programs.limit_job import limit_job


def test_no_prior_activity_allows_full_capacity():
    """With no prior jobs, a new job should be allowed with full remaining quota."""
    allowed, remaining = limit_job([], now=1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_well_below_limit_allows_job():
    """When activity is well below the limit, the job should be allowed."""
    timestamps = [990.0, 991.0, 992.0]
    allowed, remaining = limit_job(timestamps, now=1000.0, window=60, limit=10)
    assert allowed is True
    assert remaining == 7


def test_expired_timestamps_not_counted():
    """Timestamps outside the sliding window should not affect the decision."""
    old_timestamps = [800.0, 850.0, 900.0]
    allowed, remaining = limit_job(old_timestamps, now=1000.0, window=60, limit=3)
    assert allowed is True
    assert remaining == 3


def test_exceeding_limit_blocks_job():
    """When the number of recent jobs exceeds the limit, the job must be blocked."""
    timestamps = [950.0 + i for i in range(8)]
    allowed, remaining = limit_job(timestamps, now=1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """A window below the minimum should raise a ValueError."""
    with pytest.raises(ValueError):
        limit_job([], now=100.0, window=0, limit=5)


def test_at_limit_exactly_should_block():
    """When the count of recent jobs equals the limit, no more should be allowed."""
    timestamps = [960.0 + i for i in range(5)]
    allowed, remaining = limit_job(timestamps, now=1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_one_more():
    """When recent count is one less than the limit, exactly one more is allowed."""
    timestamps = [970.0 + i for i in range(4)]
    allowed, remaining = limit_job(timestamps, now=1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 1


def test_boundary_at_limit_with_mixed_timestamps():
    """Mixed old and recent timestamps at the exact limit should block the job."""
    old = [100.0, 200.0, 300.0]
    recent = [945.0, 955.0, 965.0]
    allowed, remaining = limit_job(old + recent, now=1000.0, window=60, limit=3)
    assert allowed is False
    assert remaining == 0


def test_single_job_at_unit_limit():
    """A single recent job when the limit is 1 should deny further jobs."""
    allowed, remaining = limit_job([999.0], now=1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_large_window_captures_all_timestamps():
    """A very large window should include all provided timestamps."""
    timestamps = [100.0 + i * 10 for i in range(10)]
    allowed, remaining = limit_job(timestamps, now=1000.0, window=5000, limit=10)
    assert allowed is False
    assert remaining == 0
