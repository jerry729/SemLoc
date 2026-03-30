import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.lru_evictor import lru_evictor
else:
    from programs.lru_evictor import lru_evictor


def test_eviction_when_length_equals_capacity():
    """When the number of entries equals the capacity, at least one entry should be evicted so the result is strictly under capacity."""
    order = ['a', 'b', 'c']
    result = lru_evictor(order, capacity=3)
    assert len(result) < 3


def test_exact_boundary_capacity_one():
    """A single-element list with capacity=1 should be evicted to produce an empty list."""
    order = ['x']
    result = lru_evictor(order, capacity=1)
    assert len(result) == 0
    assert result == []


def test_exact_boundary_capacity_two():
    """Two entries with capacity=2 should result in one entry after eviction."""
    order = ['oldest', 'newest']
    result = lru_evictor(order, capacity=2)
    assert len(result) < 2
    assert result == ['newest']


def test_exact_boundary_preserves_newest():
    """When len(order) == capacity, the oldest entry should be evicted, keeping the newest entries."""
    order = ['a', 'b', 'c', 'd', 'e']
    result = lru_evictor(order, capacity=5)
    assert len(result) == 4
    assert result == ['b', 'c', 'd', 'e']


def test_exact_boundary_capacity_large():
    """When 10 entries match a capacity of 10, eviction should bring the count strictly below 10."""
    order = list(range(10))
    result = lru_evictor(order, capacity=10)
    assert len(result) < 10
    assert len(result) == 9
    assert result == list(range(1, 10))


# --- Tests that pass on BOTH versions (baseline behavior) ---

def test_no_eviction_when_under_capacity():
    """When the list length is already strictly under capacity, no eviction should occur."""
    order = ['a', 'b']
    result = lru_evictor(order, capacity=5)
    assert len(result) == 2
    assert result == ['a', 'b']


def test_eviction_when_over_capacity():
    """When the list length exceeds capacity, entries are evicted from the oldest end."""
    order = ['a', 'b', 'c', 'd', 'e']
    result = lru_evictor(order, capacity=3)
    assert len(result) < 3
    assert result == ['d', 'e']


def test_negative_capacity_raises_error():
    """A negative capacity should raise a ValueError."""
    with pytest.raises(ValueError):
        lru_evictor(['a', 'b'], capacity=-1)


def test_empty_list_with_positive_capacity():
    """An empty list with a positive capacity should remain empty with no eviction."""
    order = []
    result = lru_evictor(order, capacity=5)
    assert len(result) == 0
    assert result == []