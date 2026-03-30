import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cpu_allocator import cpu_allocator
else:
    from programs.cpu_allocator import cpu_allocator


def test_equal_weights_divide_evenly():
    """Equal weights should split the total evenly when it divides cleanly."""
    result = cpu_allocator(12, [1, 1, 1])
    assert result == [4, 4, 4]


def test_single_recipient_gets_all():
    """A single recipient should receive the entire CPU pool."""
    result = cpu_allocator(100, [5])
    assert result == [100]


def test_zero_total_returns_zeros():
    """With zero total CPUs, every recipient gets zero."""
    result = cpu_allocator(0, [1, 2, 3])
    assert result == [0, 0, 0]


def test_negative_total_raises():
    """Negative total CPU pools are invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        cpu_allocator(-10, [1, 2])


def test_empty_weights_raises():
    """An empty weight list is invalid for allocation."""
    with pytest.raises(ValueError):
        cpu_allocator(10, [])


def test_total_allocation_sums_to_total_uneven_weights():
    """The sum of allocations must equal the total when weights don't divide evenly."""
    result = cpu_allocator(10, [1, 1, 1])
    assert sum(result) == 10


def test_total_preserved_with_two_thirds_split():
    """Allocating 7 CPUs with weights [1, 2] must yield a total of 7."""
    result = cpu_allocator(7, [1, 2])
    assert sum(result) == 7


def test_proportional_distribution_five_workers():
    """Five workers with unit weights splitting 11 CPUs must fully distribute them."""
    result = cpu_allocator(11, [1, 1, 1, 1, 1])
    assert sum(result) == 11
    assert all(v >= 2 for v in result)


def test_minimum_floor_applied():
    """Each recipient must receive at least the specified minimum allocation."""
    result = cpu_allocator(100, [0, 0, 0, 10], minimum=5)
    assert all(v >= 5 for v in result)


def test_large_pool_proportional_accuracy():
    """Allocating 1000 CPUs across [1, 3] should yield a 1:3 ratio summing to 1000."""
    result = cpu_allocator(1000, [1, 3])
    assert sum(result) == 1000
    assert result[0] == 250
    assert result[1] == 750
