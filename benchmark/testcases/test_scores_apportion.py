import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.scores_apportion import scores_apportion
else:
    from programs.scores_apportion import scores_apportion


def test_equal_weights_even_split():
    """Equal weights should split the total evenly among all lanes."""
    result = scores_apportion(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_lane_gets_full_total():
    """A single lane must receive the entire budget."""
    result = scores_apportion(50, [3])
    assert result == [50]


def test_zero_total_yields_all_zeros():
    """When total is zero every lane should receive zero."""
    result = scores_apportion(0, [1, 2, 3])
    assert result == [0, 0, 0]


def test_negative_total_raises():
    """Negative totals are not meaningful and must be rejected."""
    with pytest.raises(ValueError):
        scores_apportion(-10, [1, 2])


def test_empty_weights_raises():
    """An empty weight vector must be rejected."""
    with pytest.raises(ValueError):
        scores_apportion(100, [])


def test_sum_equals_total_with_unequal_weights():
    """Allocations must sum to the original total for arbitrary weights."""
    result = scores_apportion(100, [1, 1, 1])
    assert sum(result) == 100


def test_three_way_split_remainder_distributed():
    """When total is not evenly divisible, fractional units must be
    distributed so the sum still equals the total."""
    result = scores_apportion(10, [1, 1, 1])
    assert sum(result) == 10


def test_two_thirds_one_third_split():
    """A 2:1 weight ratio on a total of 10 must allocate all 10 units."""
    result = scores_apportion(10, [2, 1])
    assert sum(result) == 10
    assert result[0] > result[1]


def test_minimum_floor_applied():
    """Lanes whose proportional share falls below the minimum must be
    raised to at least the minimum value."""
    result = scores_apportion(100, [1, 1, 100], minimum=5)
    assert all(v >= 5 for v in result)


def test_large_uneven_split_preserves_total():
    """For a larger budget with many lanes the total must be preserved."""
    weights = [3, 7, 11, 13, 17]
    total = 1000
    result = scores_apportion(total, weights)
    assert sum(result) == total
