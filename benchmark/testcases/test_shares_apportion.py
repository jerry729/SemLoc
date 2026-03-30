import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shares_apportion import shares_apportion
else:
    from programs.shares_apportion import shares_apportion


def test_negative_total_raises():
    """A negative total is invalid and must be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        shares_apportion(-100, [1, 2, 3])


def test_empty_weights_raises():
    """At least one recipient weight is required."""
    with pytest.raises(ValueError, match="no weights provided"):
        shares_apportion(100, [])


def test_all_zero_weights_raises():
    """All-zero weights produce no meaningful allocation."""
    with pytest.raises(ValueError, match="all weights are zero"):
        shares_apportion(100, [0, 0, 0])


def test_equal_weights_even_split():
    """Equal weights with evenly divisible total should yield identical shares."""
    result = shares_apportion(90, [1, 1, 1])
    assert result == [30, 30, 30]


def test_single_recipient_gets_all():
    """A sole recipient must receive the entire allocation."""
    result = shares_apportion(100, [5])
    assert result == [100]


def test_total_sum_preserved_equal_thirds():
    """Allocations must sum to the original total when shares divide unevenly."""
    result = shares_apportion(100, [1, 1, 1])
    assert sum(result) == 100


def test_total_sum_preserved_varied_weights():
    """The sum of allocations equals the total even with varied proportional weights."""
    result = shares_apportion(10, [1, 2, 3])
    assert sum(result) == 10


def test_largest_remainder_distribution():
    """Residual units go to recipients with the largest fractional parts."""
    result = shares_apportion(10, [1, 1, 1])
    assert sorted(result) == [3, 3, 4] or sorted(result) == [3, 4, 3]
    assert sum(result) == 10


def test_minimum_floor_applied():
    """Each recipient receives at least the specified minimum allocation."""
    result = shares_apportion(100, [1, 1, 1, 1, 1], minimum=5)
    assert all(a >= 5 for a in result)


def test_two_recipients_uneven():
    """Two recipients with 1:3 ratio over 100 units should sum correctly."""
    result = shares_apportion(100, [1, 3])
    assert sum(result) == 100
    assert result[0] == 25
    assert result[1] == 75
