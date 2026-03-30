import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.tasks_allocator import tasks_allocator
else:
    from programs.tasks_allocator import tasks_allocator


def test_equal_weights_even_split():
    """Equal weights should produce equal allocations when total is evenly divisible."""
    result = tasks_allocator(12, [1, 1, 1])
    assert result == [4, 4, 4]


def test_zero_total_yields_zeros():
    """A total of zero should allocate nothing to any recipient."""
    result = tasks_allocator(0, [3, 7])
    assert result == [0, 0]


def test_single_recipient_gets_all():
    """A single recipient should receive the entire total."""
    result = tasks_allocator(100, [5])
    assert result == [100]


def test_negative_total_raises():
    """Negative totals are invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        tasks_allocator(-1, [1, 1])


def test_empty_weights_raises():
    """An empty weights list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="no weights"):
        tasks_allocator(10, [])


def test_sum_of_allocations_equals_total_simple():
    """The sum of all allocations must equal the original total for straightforward splits."""
    result = tasks_allocator(10, [1, 1, 1, 1, 1])
    assert sum(result) == 10


def test_sum_of_allocations_with_unequal_weights():
    """Proportional allocation must preserve the total even when weights differ."""
    result = tasks_allocator(10, [1, 2, 3])
    assert sum(result) == 10


def test_sum_preserved_with_three_recipients():
    """Distributing 7 among 3 equal recipients must still sum to 7."""
    result = tasks_allocator(7, [1, 1, 1])
    assert sum(result) == 7


def test_minimum_floor_respected():
    """Every recipient must receive at least the specified minimum allocation."""
    result = tasks_allocator(100, [1, 1, 1, 1], minimum=10)
    assert all(x >= 10 for x in result)


def test_large_total_sum_preserved():
    """Allocation of a large total across many recipients must preserve the sum."""
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = tasks_allocator(1000, weights)
    assert sum(result) == 1000
