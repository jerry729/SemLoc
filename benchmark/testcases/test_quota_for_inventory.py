import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, "inst", None):
    from instrumented.quota_for_inventory import quota_for_inventory
else:
    from programs.quota_for_inventory import quota_for_inventory


def test_negative_total_raises():
    """A negative inventory total is invalid and must be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        quota_for_inventory(-10, [1, 2, 3])


def test_empty_weights_raises():
    """An empty weight list means no recipients and must be rejected."""
    with pytest.raises(ValueError, match="no weights provided"):
        quota_for_inventory(100, [])


def test_all_zero_weights_raises():
    """All-zero weights are meaningless and must be rejected."""
    with pytest.raises(ValueError, match="all weights are zero"):
        quota_for_inventory(100, [0, 0, 0])


def test_single_recipient_gets_all():
    """A single recipient should receive the entire inventory."""
    result = quota_for_inventory(100, [5])
    assert result == [100]


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total yields equal shares."""
    result = quota_for_inventory(90, [1, 1, 1])
    assert result == [30, 30, 30]


def test_total_allocation_preserves_sum_simple():
    """The sum of allocations should equal the original total when total is an integer and weights divide evenly."""
    result = quota_for_inventory(100, [1, 1, 1, 1])
    assert sum(result) == 100


def test_total_allocation_preserves_sum_uneven():
    """The sum of allocated units must equal the available inventory even when proportional shares are fractional."""
    result = quota_for_inventory(10, [1, 1, 1])
    assert sum(result) == 10


def test_two_recipients_uneven_weights():
    """With weights 1 and 2, the second recipient should get roughly twice as much, and all units are distributed."""
    result = quota_for_inventory(10, [1, 2])
    assert sum(result) == 10
    assert result[1] >= result[0]


def test_minimum_floor_applied():
    """Each recipient must receive at least the specified minimum allocation."""
    result = quota_for_inventory(100, [1, 1, 1, 1, 1], minimum=5)
    assert all(a >= 5 for a in result)


def test_large_group_sum_preserved():
    """Distributing 1000 units across 7 unequal weights must preserve the total count."""
    weights = [3, 7, 2, 5, 11, 4, 1]
    result = quota_for_inventory(1000, weights)
    assert sum(result) == 1000
