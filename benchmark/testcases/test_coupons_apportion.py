import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.coupons_apportion import coupons_apportion
else:
    from programs.coupons_apportion import coupons_apportion


def test_empty_weights_raises():
    """An empty weight list must be rejected with a ValueError."""
    with pytest.raises(ValueError, match="weights required"):
        coupons_apportion(100, [])


def test_negative_total_raises():
    """A negative total is not a valid coupon budget."""
    with pytest.raises(ValueError, match="negative total"):
        coupons_apportion(-5, [1, 2, 3])


def test_zero_weight_sum_raises():
    """Weights summing to zero cannot define a proportion."""
    with pytest.raises(ValueError, match="zero total weight"):
        coupons_apportion(100, [0, 0, 0])


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total should yield uniform shares."""
    result = coupons_apportion(90, [1, 1, 1])
    assert result == [30, 30, 30]


def test_single_recipient_gets_all():
    """A single recipient receives the entire allocation."""
    result = coupons_apportion(42, [5])
    assert result == [42]


def test_integer_allocation_sums_to_total():
    """Integer allocations must sum exactly to the requested total when no minimum is applied."""
    total = 100
    weights = [1, 2, 3, 4]
    result = coupons_apportion(total, weights)
    assert sum(result) == total


def test_uneven_weights_sum_preserved():
    """The sum of integer allocations must equal total for weights that don't divide evenly."""
    total = 10
    weights = [1, 1, 1]
    result = coupons_apportion(total, weights)
    assert sum(result) == total


def test_large_prime_total_distributed_exactly():
    """A prime total that doesn't divide evenly must still sum correctly across recipients."""
    total = 97
    weights = [3, 7, 11]
    result = coupons_apportion(total, weights)
    assert sum(result) == total


def test_float_mode_preserves_exact_proportions():
    """When floor_to_int is False, shares should be exact float proportions."""
    result = coupons_apportion(100, [1, 3], floor_to_int=False)
    assert abs(result[0] - 25.0) < 1e-9
    assert abs(result[1] - 75.0) < 1e-9


def test_minimum_guarantee_applied():
    """Recipients whose proportional share is below minimum must receive the minimum."""
    result = coupons_apportion(100, [1, 99], floor_to_int=False, minimum=5)
    assert result[0] >= 5
