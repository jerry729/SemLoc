import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_points_share import plan_points_share
else:
    from programs.plan_points_share import plan_points_share


def test_equal_weights_even_split():
    """When all weights are equal the points should be evenly distributed."""
    result = plan_points_share(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_lane_gets_all_points():
    """A single lane should receive the entire budget."""
    result = plan_points_share(50, [3])
    assert result == [50]


def test_negative_total_raises():
    """Negative total budget must be rejected."""
    with pytest.raises(ValueError):
        plan_points_share(-10, [1, 2])


def test_empty_weights_raises():
    """Empty weight vector must be rejected."""
    with pytest.raises(ValueError):
        plan_points_share(100, [])


def test_zero_total_returns_zeros():
    """A zero budget should allocate zero to every lane."""
    result = plan_points_share(0, [1, 2, 3])
    assert result == [0, 0, 0]


def test_total_is_preserved_with_equal_weights():
    """The sum of allocations must equal the original total when weights are equal."""
    total = 100
    result = plan_points_share(total, [1, 1, 1, 1, 1])
    assert sum(result) == total


def test_total_preserved_with_uneven_weights():
    """The sum of allocations must equal the original total for arbitrary weights."""
    total = 100
    result = plan_points_share(total, [1, 2, 3])
    assert sum(result) == total


def test_three_way_split_preserves_total():
    """Splitting 10 points three ways should still sum to 10."""
    result = plan_points_share(10, [1, 1, 1])
    assert sum(result) == 10


def test_large_total_proportional_allocation():
    """For large totals the allocation must reflect weight proportions and preserve the budget."""
    total = 1000
    weights = [1, 2, 3, 4]
    result = plan_points_share(total, weights)
    assert sum(result) == total
    assert result[3] > result[0]


def test_minimum_floor_applied():
    """Lanes with tiny weight should still receive at least the minimum allocation."""
    result = plan_points_share(100, [100, 1], minimum=5)
    assert result[1] >= 5
