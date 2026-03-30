import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quota_for_fuel import quota_for_fuel
else:
    from programs.quota_for_fuel import quota_for_fuel


def test_negative_total_raises():
    """Negative fuel totals are rejected as invalid."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        quota_for_fuel(-10, [1, 2, 3])


def test_empty_weights_raises():
    """An empty weight list is invalid for allocation."""
    with pytest.raises(ValueError, match="no weights provided"):
        quota_for_fuel(100, [])


def test_all_zero_weights_raises():
    """All-zero weights make proportional allocation undefined."""
    with pytest.raises(ValueError, match="all weights are zero"):
        quota_for_fuel(100, [0, 0, 0])


def test_equal_weights_divide_evenly():
    """Equal weights should distribute fuel evenly among recipients."""
    result = quota_for_fuel(90, [1, 1, 1])
    assert result == [30, 30, 30]


def test_single_recipient_gets_all():
    """A single recipient should receive the entire allocation."""
    result = quota_for_fuel(100, [5])
    assert result == [100]


def test_total_allocation_conserved_three_way():
    """Total allocated fuel must equal the total available when weights split unevenly."""
    result = quota_for_fuel(100, [1, 1, 1])
    assert sum(result) == 100


def test_total_allocation_conserved_two_thirds():
    """With weights [1, 2], the allocated total must equal the input total."""
    result = quota_for_fuel(10, [1, 2])
    assert sum(result) == 10


def test_proportional_split_with_remainder():
    """Seven units split among three equal weights should distribute the remainder fairly."""
    result = quota_for_fuel(7, [1, 1, 1])
    assert sum(result) == 7
    assert all(x in (2, 3) for x in result)


def test_minimum_floor_applied():
    """Each recipient must receive at least the specified minimum allocation."""
    result = quota_for_fuel(100, [1, 1, 1, 1, 1], minimum=5)
    assert all(x >= 5 for x in result)


def test_large_unequal_weights_conserve_total():
    """Conservation of total fuel must hold for large unequal weight vectors."""
    weights = [3, 7, 11, 13, 17]
    total = 1000
    result = quota_for_fuel(total, weights)
    assert sum(result) == total
