import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_tickets_share import plan_tickets_share
else:
    from programs.plan_tickets_share import plan_tickets_share


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total yield identical shares."""
    result = plan_tickets_share(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_bucket_gets_all():
    """A single weight entry receives the entire total."""
    result = plan_tickets_share(50, [3])
    assert result == [50]


def test_float_mode_preserves_fractions():
    """With floor_to_int=False fractional allocations are preserved."""
    result = plan_tickets_share(10, [1, 1, 1], floor_to_int=False)
    for v in result:
        assert abs(v - 10 / 3) < 1e-9


def test_empty_weights_raises():
    """Empty weight list must raise ValueError."""
    with pytest.raises(ValueError, match="weights required"):
        plan_tickets_share(100, [])


def test_negative_total_raises():
    """A negative total capacity is invalid."""
    with pytest.raises(ValueError, match="negative total"):
        plan_tickets_share(-1, [1, 2])


def test_integer_allocation_sums_to_total_three_buckets():
    """Integer allocations must sum exactly to total when no minimums apply."""
    result = plan_tickets_share(10, [1, 1, 1])
    assert sum(result) == 10


def test_integer_allocation_sums_to_total_unequal_weights():
    """Unequal weights should still produce allocations summing to total."""
    result = plan_tickets_share(100, [1, 2, 3])
    assert sum(result) == 100


def test_integer_allocation_sums_to_total_large():
    """Many buckets with a large total must preserve the total sum."""
    weights = [1, 2, 3, 4, 5, 6, 7]
    result = plan_tickets_share(1000, weights)
    assert sum(result) == 1000


def test_minimum_floor_applied():
    """Buckets with very small proportional share receive the minimum."""
    result = plan_tickets_share(100, [100, 1], minimum=5)
    assert result[1] >= 5


def test_two_equal_weights_odd_total():
    """Two equal weights splitting an odd total should still sum correctly."""
    result = plan_tickets_share(7, [1, 1])
    assert sum(result) == 7
