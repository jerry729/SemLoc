import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.plan_seats_share import plan_seats_share
else:
    from programs.plan_seats_share import plan_seats_share


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total should yield identical allocations."""
    result = plan_seats_share(10, [1, 1, 1, 1, 1])
    assert result == [2, 2, 2, 2, 2]


def test_single_party_gets_all():
    """A single party must receive the entire allocation."""
    result = plan_seats_share(100, [5])
    assert result == [100]


def test_empty_weights_raises():
    """Allocation requires at least one party."""
    with pytest.raises(ValueError, match="weights required"):
        plan_seats_share(10, [])


def test_negative_total_raises():
    """A negative total capacity is invalid."""
    with pytest.raises(ValueError, match="negative total"):
        plan_seats_share(-5, [1, 2])


def test_float_mode_returns_exact_proportions():
    """When integer flooring is disabled, proportions should be exact floats."""
    result = plan_seats_share(10, [1, 1, 1], floor_to_int=False)
    for v in result:
        assert abs(v - 10 / 3) < 1e-9


def test_integer_allocation_sums_to_total():
    """Integer allocations must sum to the total seats when shares are not trivially even."""
    result = plan_seats_share(10, [1, 1, 1])
    assert sum(result) == 10


def test_largest_remainder_distribution_three_parties():
    """Three parties sharing 10 seats: the leftover seat is given by largest remainder."""
    result = plan_seats_share(10, [1, 1, 1])
    assert sorted(result) == [3, 3, 4] or sorted(result) == [3, 3, 4]
    assert sum(result) == 10


def test_two_unequal_weights_sum_preserved():
    """Two parties with 1:2 ratio sharing 10 seats must sum to 10."""
    result = plan_seats_share(10, [1, 2])
    assert sum(result) == 10


def test_five_parties_seven_seats():
    """Five equally weighted parties sharing 7 seats must sum to 7."""
    result = plan_seats_share(7, [1, 1, 1, 1, 1])
    assert sum(result) == 7


def test_minimum_floor_applied():
    """Parties whose proportional share falls below the minimum receive the minimum."""
    result = plan_seats_share(100, [1, 1, 100], minimum=5, floor_to_int=False)
    assert all(v >= 5 for v in result)
