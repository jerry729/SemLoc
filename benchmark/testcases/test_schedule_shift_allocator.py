import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.schedule_shift_allocator import schedule_shift_allocator
else:
    from programs.schedule_shift_allocator import schedule_shift_allocator


def test_equal_weights_even_split():
    """When all weights are equal and total divides evenly, every worker gets the same share."""
    result = schedule_shift_allocator(12, [1, 1, 1])
    assert result == [4, 4, 4]


def test_single_worker_gets_all():
    """A single worker should receive the entire total."""
    result = schedule_shift_allocator(10, [5])
    assert result == [10]


def test_zero_total_yields_zeros():
    """With zero total and no minimum, all allocations should be zero."""
    result = schedule_shift_allocator(0, [3, 7])
    assert result == [0, 0]


def test_negative_total_raises():
    """Negative total shifts are not meaningful and should be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        schedule_shift_allocator(-1, [1, 2])


def test_empty_weights_raises():
    """An empty weight list has no workers to allocate to."""
    with pytest.raises(ValueError, match="invalid weights"):
        schedule_shift_allocator(10, [])


def test_allocations_sum_to_total_uniform():
    """The sum of allocated shifts must equal the requested total for uniform weights."""
    result = schedule_shift_allocator(10, [1, 1, 1])
    assert sum(result) == 10


def test_allocations_sum_to_total_varied_weights():
    """The sum of allocated shifts must equal the requested total for varied weights."""
    result = schedule_shift_allocator(100, [1, 2, 3, 4])
    assert sum(result) == 100


def test_allocations_sum_to_total_with_minimum():
    """The total allocation should be preserved even when a minimum floor is applied."""
    result = schedule_shift_allocator(20, [1, 1, 1, 1, 1], minimum=2)
    assert sum(result) == 20


def test_fractional_distribution_preserves_total():
    """Proportional weights that produce fractional shares must still sum to the total after rounding."""
    result = schedule_shift_allocator(7, [1, 1, 1])
    assert sum(result) == 7


def test_large_total_proportional_accuracy():
    """With a large total, heavier weights should receive proportionally more shifts."""
    result = schedule_shift_allocator(1000, [1, 3, 6])
    assert sum(result) == 1000
    assert result[2] > result[1] > result[0]
