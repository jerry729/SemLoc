import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_jobs_share import plan_jobs_share
else:
    from programs.plan_jobs_share import plan_jobs_share


def test_equal_weights_even_split():
    """Equal weights should divide capacity evenly across all jobs."""
    result = plan_jobs_share(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_job_gets_full_capacity():
    """A single job should receive the entire capacity."""
    result = plan_jobs_share(50, [3])
    assert result == [50]


def test_empty_weights_raises():
    """An empty weight list is not a valid allocation request."""
    with pytest.raises(ValueError, match="weights required"):
        plan_jobs_share(100, [])


def test_negative_total_raises():
    """Negative total capacity is not allowed."""
    with pytest.raises(ValueError, match="negative total"):
        plan_jobs_share(-10, [1, 2])


def test_float_mode_preserves_fractions():
    """With floor_to_int disabled, fractional shares are preserved."""
    result = plan_jobs_share(10, [1, 1, 1], floor_to_int=False)
    for v in result:
        assert abs(v - 10.0 / 3.0) < 1e-9


def test_total_allocation_sums_to_total():
    """Integer allocations must sum to the total capacity."""
    result = plan_jobs_share(10, [1, 1, 1])
    assert sum(result) == 10


def test_weighted_allocation_preserves_total():
    """When weights differ, the integer allocations should still sum to the total."""
    result = plan_jobs_share(100, [1, 2, 3])
    assert sum(result) == 100


def test_two_jobs_unequal_weights_sum():
    """Two jobs with 1:3 ratio sharing 10 units must sum to 10."""
    result = plan_jobs_share(10, [1, 3])
    assert sum(result) == 10


def test_five_jobs_remainder_distribution():
    """Five equal-weight jobs sharing 13 units should distribute the remainder."""
    result = plan_jobs_share(13, [1, 1, 1, 1, 1])
    assert sum(result) == 13
    assert all(v >= 2 for v in result)


def test_minimum_floor_applied():
    """Jobs whose proportional share falls below the minimum receive the minimum."""
    result = plan_jobs_share(100, [1, 1], floor_to_int=False, minimum=60)
    assert all(v >= 60 for v in result)
