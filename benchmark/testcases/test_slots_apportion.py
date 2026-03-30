import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.slots_apportion import slots_apportion
else:
    from programs.slots_apportion import slots_apportion


def test_negative_total_raises():
    """A negative total is meaningless for slot distribution and must be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        slots_apportion(-5, [1, 2, 3])


def test_empty_weights_raises():
    """At least one recipient must be specified."""
    with pytest.raises(ValueError, match="no weights provided"):
        slots_apportion(10, [])


def test_all_zero_weights_raises():
    """All-zero weights cannot define a proportion and must be rejected."""
    with pytest.raises(ValueError, match="all weights are zero"):
        slots_apportion(10, [0, 0, 0])


def test_single_recipient_gets_all():
    """A single recipient should receive the entire allocation."""
    result = slots_apportion(100, [1])
    assert result == [100]


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total should produce equal allocations."""
    result = slots_apportion(12, [1, 1, 1])
    assert result == [4, 4, 4]


def test_total_preserved_with_uneven_weights():
    """The sum of allocations must equal the original total when no minimum is applied."""
    result = slots_apportion(10, [1, 1, 1])
    assert sum(result) == 10


def test_total_preserved_two_recipients():
    """Distributing 7 slots among 2 equal recipients must still sum to 7."""
    result = slots_apportion(7, [1, 1])
    assert sum(result) == 7


def test_proportional_distribution_three_way():
    """Allocations should reflect the weight proportions with remainder distributed."""
    result = slots_apportion(100, [1, 2, 7])
    assert sum(result) == 100
    assert result[2] >= result[1] >= result[0]


def test_minimum_guarantee_applied():
    """Each recipient must receive at least the specified minimum, and total must be preserved."""
    result = slots_apportion(30, [0, 0, 0, 10], minimum=2)
    for alloc in result:
        assert alloc >= 2
    assert sum(result) == round(sum(max(2, (w / 10) * 30) for w in [0, 0, 0, 10]))


def test_large_allocation_preserves_total():
    """Apportionment of a large total across many recipients must preserve the total count."""
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    total = 1000
    result = slots_apportion(total, weights)
    assert sum(result) == total
