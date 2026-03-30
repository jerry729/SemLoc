import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quota_for_capacity import quota_for_capacity
else:
    from programs.quota_for_capacity import quota_for_capacity


def test_empty_weights_raises():
    """An allocation request with no weight entries must be rejected."""
    with pytest.raises(ValueError, match="weights required"):
        quota_for_capacity(100, [])


def test_negative_total_raises():
    """Negative total capacity is invalid for resource provisioning."""
    with pytest.raises(ValueError, match="negative total"):
        quota_for_capacity(-10, [1, 2, 3])


def test_zero_weight_sum_raises():
    """All-zero weights cannot meaningfully partition capacity."""
    with pytest.raises(ValueError, match="zero total weight"):
        quota_for_capacity(100, [0, 0, 0])


def test_equal_weights_float_mode():
    """Equal weights should produce equal shares in float mode."""
    result = quota_for_capacity(90, [1, 1, 1], floor_to_int=False)
    assert len(result) == 3
    for v in result:
        assert abs(v - 30.0) < 1e-9


def test_single_slot_receives_all():
    """A single slot must receive the entire capacity."""
    result = quota_for_capacity(42, [5])
    assert result == [42]


def test_integer_allocations_sum_equals_total_even_split():
    """Integer allocations for evenly divisible capacity must sum to total."""
    result = quota_for_capacity(100, [1, 1, 1, 1])
    assert sum(result) == 100


def test_integer_allocations_sum_equals_total_uneven():
    """Integer allocations must preserve total even when weights cause remainders."""
    result = quota_for_capacity(10, [1, 1, 1])
    assert sum(result) == 10


def test_three_way_split_of_100():
    """Splitting 100 units three ways must yield a total of 100 integer units."""
    result = quota_for_capacity(100, [1, 1, 1])
    assert sum(result) == 100
    assert all(isinstance(v, int) for v in result)


def test_weighted_split_preserves_total():
    """Asymmetric weights must still sum allocated units to total capacity."""
    result = quota_for_capacity(50, [3, 1, 1])
    assert sum(result) == 50


def test_large_capacity_preserves_total():
    """Integer rounding across many slots must not leak capacity."""
    weights = [1, 2, 3, 4, 5, 6, 7]
    result = quota_for_capacity(1000, weights)
    assert sum(result) == 1000
    assert all(isinstance(v, int) for v in result)
