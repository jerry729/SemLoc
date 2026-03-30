import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quota_for_storage import quota_for_storage
else:
    from programs.quota_for_storage import quota_for_storage


def test_equal_weights_even_split():
    """Equal weights should distribute total evenly among recipients."""
    result = quota_for_storage(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_zero_total_yields_all_zeros():
    """A total of zero should produce zero allocations for every recipient."""
    result = quota_for_storage(0, [3, 5, 2])
    assert result == [0, 0, 0]


def test_single_recipient_gets_everything():
    """A single recipient should receive the full total."""
    result = quota_for_storage(500, [7])
    assert result == [500]


def test_negative_total_raises():
    """Negative totals are invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        quota_for_storage(-10, [1, 2])


def test_empty_weights_raises():
    """An empty weight list is not a valid allocation request."""
    with pytest.raises(ValueError, match="no weights provided"):
        quota_for_storage(100, [])


def test_allocation_sum_equals_total_three_way():
    """The sum of integer allocations must equal the distributable total."""
    result = quota_for_storage(100, [1, 1, 1])
    assert sum(result) == 100


def test_allocation_sum_with_unequal_weights():
    """Total allocated units must equal the requested total even with unequal weights."""
    result = quota_for_storage(10, [1, 2, 3])
    assert sum(result) == 10


def test_remainder_distributed_correctly():
    """When total does not divide evenly, remainder units are assigned to highest-fraction recipients."""
    result = quota_for_storage(10, [1, 1, 1])
    assert sum(result) == 10
    assert sorted(result) == [3, 3, 4]


def test_minimum_allocation_enforced():
    """Each recipient must receive at least the specified minimum allocation."""
    result = quota_for_storage(100, [0, 0, 0, 10], minimum=5)
    assert all(a >= 5 for a in result)


def test_large_equal_split_preserves_total():
    """Proportional allocation across many recipients must still sum to the total."""
    weights = [1] * 7
    result = quota_for_storage(100, weights)
    assert sum(result) == 100
