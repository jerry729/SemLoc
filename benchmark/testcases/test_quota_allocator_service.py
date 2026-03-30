import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.quota_allocator_service import quota_allocator_service
else:
    from programs.quota_allocator_service import quota_allocator_service


def test_negative_total_raises():
    """A negative total quota pool is nonsensical and must be rejected."""
    with pytest.raises(ValueError, match="total must be non-negative"):
        quota_allocator_service(-10, [1, 2, 3])


def test_negative_minimum_raises():
    """A negative per-consumer minimum is invalid."""
    with pytest.raises(ValueError, match="minimum must be non-negative"):
        quota_allocator_service(100, [1, 1], minimum=-5)


def test_empty_weights_raises():
    """At least one consumer weight must be provided."""
    with pytest.raises(ValueError):
        quota_allocator_service(100, [])


def test_equal_weights_even_split():
    """Equal weights with an evenly divisible total should yield identical shares."""
    result = quota_allocator_service(100, [1, 1, 1, 1])
    assert result == [25, 25, 25, 25]


def test_single_consumer_gets_all():
    """A single consumer should receive the entire quota."""
    result = quota_allocator_service(50, [7])
    assert result == [50]


def test_total_allocation_matches_pool_equal_weights():
    """The sum of allocations must equal the total quota when weights divide evenly."""
    result = quota_allocator_service(120, [1, 1, 1])
    assert sum(result) == 120


def test_total_allocation_matches_pool_unequal_weights():
    """The sum of integer allocations must equal the rounded total when weights are unequal."""
    total = 100
    weights = [1, 2, 3]
    result = quota_allocator_service(total, weights)
    assert sum(result) == total


def test_fractional_quotas_round_correctly():
    """When proportional shares are non-integer the largest-remainder method distributes leftover units."""
    result = quota_allocator_service(10, [1, 1, 1])
    assert sum(result) == 10
    assert all(v >= 3 for v in result)


def test_minimum_guarantee_with_small_weight():
    """A consumer with a tiny weight must still receive at least the minimum allocation."""
    result = quota_allocator_service(100, [100, 1], minimum=10)
    assert result[1] >= 10


def test_seven_consumers_total_preserved():
    """With seven consumers the total pool must be fully allocated after rounding."""
    total = 100
    weights = [3, 7, 2, 5, 1, 4, 8]
    result = quota_allocator_service(total, weights)
    assert sum(result) == total
