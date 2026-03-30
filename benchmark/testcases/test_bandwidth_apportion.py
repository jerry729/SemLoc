import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bandwidth_apportion import bandwidth_apportion
else:
    from programs.bandwidth_apportion import bandwidth_apportion


def test_equal_weights_divide_evenly():
    """Equal weights with an evenly divisible total should yield uniform allocations."""
    result = bandwidth_apportion(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_negative_total_raises():
    """A negative total bandwidth is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        bandwidth_apportion(-10, [1, 2])


def test_empty_weights_raises():
    """An empty weight vector must raise ValueError."""
    with pytest.raises(ValueError):
        bandwidth_apportion(100, [])


def test_all_zero_weights_raises():
    """All-zero weights are degenerate and must raise ValueError."""
    with pytest.raises(ValueError):
        bandwidth_apportion(100, [0, 0, 0])


def test_single_consumer_gets_all():
    """A single consumer should receive the entire bandwidth budget."""
    result = bandwidth_apportion(500, [3])
    assert result == [500]


def test_total_allocation_preserves_budget_two_consumers():
    """The sum of allocations must equal the total available bandwidth."""
    result = bandwidth_apportion(100, [1, 2])
    assert sum(result) == 100


def test_total_allocation_preserves_budget_three_unequal():
    """Unequal three-way split must still sum to the total bandwidth."""
    result = bandwidth_apportion(10, [1, 1, 1])
    assert sum(result) == 10


def test_fractional_remainders_distributed():
    """When the total cannot split evenly, leftover units are distributed by largest remainder."""
    result = bandwidth_apportion(100, [1, 1, 1])
    assert sum(result) == 100
    assert all(x in (33, 34) for x in result)


def test_minimum_guarantee_with_remainder_conservation():
    """Minimum guarantees must be respected while conserving total bandwidth."""
    result = bandwidth_apportion(100, [1, 1, 1], minimum=5)
    assert all(x >= 5 for x in result)
    assert sum(result) == 100


def test_weighted_split_seven_three():
    """A 70/30 weighted split of 100 units must sum to the total."""
    result = bandwidth_apportion(100, [7, 3])
    assert sum(result) == 100
    assert result[0] == 70
    assert result[1] == 30
