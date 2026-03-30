import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.budget_budgeter import budget_budgeter
else:
    from programs.budget_budgeter import budget_budgeter


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total should give identical shares."""
    result = budget_budgeter(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_recipient_gets_full_budget():
    """A single recipient should receive the entire budget."""
    result = budget_budgeter(500, [3])
    assert result == [500]


def test_zero_total_gives_zero_allocations():
    """With zero budget and no minimum, every allocation must be zero."""
    result = budget_budgeter(0, [1, 2, 3])
    assert result == [0, 0, 0]


def test_negative_total_raises():
    """A negative total is an invalid input and should raise ValueError."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        budget_budgeter(-10, [1, 2])


def test_empty_weights_raises():
    """Empty weight list is invalid and must raise ValueError."""
    with pytest.raises(ValueError, match="no weights provided"):
        budget_budgeter(100, [])


def test_total_allocation_equals_budget_three_way():
    """The sum of integer allocations should equal the total budget for a three-way split."""
    result = budget_budgeter(100, [1, 1, 1])
    assert sum(result) == 100


def test_total_allocation_preserves_budget_uneven():
    """Uneven weights must still distribute exactly the full budget across recipients."""
    result = budget_budgeter(10, [1, 1, 1])
    assert sum(result) == 10


def test_two_recipients_odd_total():
    """Splitting an odd total between two equal-weight recipients should still sum correctly."""
    result = budget_budgeter(7, [1, 1])
    assert sum(result) == 7


def test_weighted_split_preserves_budget():
    """A weighted split with non-trivial remainders must still total the original budget."""
    result = budget_budgeter(1000, [3, 3, 4])
    assert sum(result) == 1000


def test_minimum_floor_applied():
    """Each recipient must receive at least the minimum even if proportional share is smaller."""
    result = budget_budgeter(100, [0, 0, 0, 10], minimum=5)
    for alloc in result:
        assert alloc >= 5
