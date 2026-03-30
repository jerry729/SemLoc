import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quota_for_memory import quota_for_memory
else:
    from programs.quota_for_memory import quota_for_memory


def test_equal_weights_exact_division():
    """When total divides evenly among equal-weight recipients each gets an equal share."""
    result = quota_for_memory(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_recipient_gets_all():
    """A single recipient should receive the entire allocation."""
    result = quota_for_memory(1024, [5])
    assert result == [1024]


def test_zero_total_yields_zeros():
    """Allocating zero memory should give every recipient zero units."""
    result = quota_for_memory(0, [3, 7])
    assert result == [0, 0]


def test_negative_total_raises():
    """Negative total memory is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        quota_for_memory(-10, [1, 2])


def test_empty_weights_raises():
    """An empty weight list is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        quota_for_memory(100, [])


def test_total_allocation_matches_total_even_split():
    """Sum of allocated units must equal the total when weights divide evenly."""
    result = quota_for_memory(90, [1, 1, 1])
    assert sum(result) == 90


def test_total_allocation_preserved_uneven_weights():
    """Sum of allocated units must equal the total for non-uniform weights."""
    result = quota_for_memory(10, [1, 1, 1])
    assert sum(result) == 10


def test_total_allocation_preserved_large_group():
    """Sum of allocations must equal total for a larger set of recipients."""
    weights = [1, 2, 3, 4, 5, 6, 7]
    result = quota_for_memory(100, weights)
    assert sum(result) == 100


def test_minimum_guarantee_applied():
    """Every recipient must receive at least the specified minimum allocation."""
    result = quota_for_memory(100, [1, 1, 1, 1, 1], minimum=5)
    assert all(a >= 5 for a in result)


def test_fractional_rounding_preserves_total():
    """Allocations with fractional proportions must still sum to the total."""
    result = quota_for_memory(7, [1, 1, 1])
    assert sum(result) == 7
