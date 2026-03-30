import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.credits_allocator import credits_allocator
else:
    from programs.credits_allocator import credits_allocator


def test_negative_total_raises():
    """A negative credit pool is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        credits_allocator(-10, [1, 2, 3])


def test_empty_weights_raises():
    """At least one recipient must be specified."""
    with pytest.raises(ValueError):
        credits_allocator(100, [])


def test_all_zero_weights_raises():
    """All-zero weight vectors are meaningless and must be rejected."""
    with pytest.raises(ValueError):
        credits_allocator(100, [0, 0, 0])


def test_equal_weights_even_split():
    """Equal weights with a cleanly divisible total should yield uniform allocation."""
    result = credits_allocator(30, [1, 1, 1])
    assert result == [10, 10, 10]


def test_single_recipient_gets_all():
    """A single recipient should receive the entire credit pool."""
    result = credits_allocator(100, [5])
    assert result == [100]


def test_total_allocation_preserves_sum_equal_weights():
    """The sum of allocated credits must equal the original total for equal weights."""
    result = credits_allocator(100, [1, 1, 1])
    assert sum(result) == 100


def test_total_allocation_preserves_sum_unequal_weights():
    """The sum of allocated credits must equal the total for unequal weight distributions."""
    result = credits_allocator(10, [1, 1, 1])
    assert sum(result) == 10


def test_proportional_split_two_recipients():
    """Two recipients with 1:3 weights sharing 100 credits should get 25 and 75."""
    result = credits_allocator(100, [1, 3])
    assert result == [25, 75]


def test_remainder_distributed_correctly():
    """When 10 credits are split among 3 equal recipients the remainder must still be allocated."""
    result = credits_allocator(10, [1, 1, 1])
    assert sum(result) == 10
    assert all(x in (3, 4) for x in result)


def test_minimum_floor_applied():
    """Recipients with very low weight must still receive at least the minimum allocation."""
    result = credits_allocator(100, [100, 1, 1], minimum=5)
    assert all(x >= 5 for x in result)
