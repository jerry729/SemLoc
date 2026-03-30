import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bandwidth_budgeter import bandwidth_budgeter
else:
    from programs.bandwidth_budgeter import bandwidth_budgeter


def test_equal_weights_exact_division():
    """When weights are equal and total divides evenly, each recipient gets the same share."""
    result = bandwidth_budgeter(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_negative_total_raises():
    """A negative bandwidth budget is invalid and must be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        bandwidth_budgeter(-10, [1, 2])


def test_empty_weights_raises():
    """At least one recipient weight must be provided."""
    with pytest.raises(ValueError, match="no weights provided"):
        bandwidth_budgeter(100, [])


def test_all_zero_weights_raises():
    """If every weight is zero, allocation is undefined and must be rejected."""
    with pytest.raises(ValueError, match="all weights are zero"):
        bandwidth_budgeter(100, [0, 0, 0])


def test_single_recipient_gets_full_budget():
    """A single recipient should receive the entire bandwidth budget."""
    result = bandwidth_budgeter(99, [5])
    assert result == [99]


def test_total_allocation_equals_budget_two_recipients():
    """The sum of allocations must equal the total budget when no minimum is set."""
    result = bandwidth_budgeter(10, [1, 2])
    assert sum(result) == 10


def test_total_allocation_three_recipients_non_trivial():
    """Allocations across three recipients must sum to the original budget."""
    result = bandwidth_budgeter(100, [1, 1, 1])
    assert sum(result) == 100


def test_unequal_weights_preserve_total():
    """Even with unequal weights producing fractional shares, the budget is fully distributed."""
    result = bandwidth_budgeter(10, [1, 1, 1])
    assert sum(result) == 10


def test_minimum_floor_applied():
    """Recipients with negligible weight still receive at least the minimum allocation."""
    result = bandwidth_budgeter(100, [100, 1], minimum=10)
    assert result[1] >= 10


def test_proportional_ordering_respected():
    """A recipient with higher weight should receive at least as much as one with lower weight."""
    result = bandwidth_budgeter(1000, [3, 1, 2])
    assert result[0] >= result[2] >= result[1]
    assert sum(result) == 1000
