import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.combine_requests import combine_requests
else:
    from programs.combine_requests import combine_requests


def test_disjoint_streams():
    """Non-overlapping streams should concatenate in sorted order."""
    result = combine_requests([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_empty_left_stream():
    """An empty left stream should yield the right stream unchanged."""
    result = combine_requests([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_empty_right_stream():
    """An empty right stream should yield the left stream unchanged."""
    result = combine_requests([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_both_empty():
    """Two empty streams should produce an empty result."""
    result = combine_requests([], [])
    assert result == []


def test_single_element_each_different():
    """Single-element non-equal streams should merge correctly."""
    result = combine_requests([1], [2])
    assert result == [1, 2]


def test_duplicate_elements_at_end():
    """When both streams share the same last element, both copies must be retained."""
    result = combine_requests([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_fully_overlapping_streams():
    """Identical streams should produce every element twice in sorted order."""
    result = combine_requests([2, 4, 6], [2, 4, 6])
    assert result == [2, 2, 4, 4, 6, 6]


def test_single_shared_element():
    """A shared element between single-element streams must appear twice."""
    result = combine_requests([7], [7])
    assert result == [7, 7]


def test_shared_tail_with_longer_streams():
    """All duplicate entries at the tail of two streams must be preserved."""
    result = combine_requests([1, 2, 3, 10], [5, 8, 10])
    assert result == [1, 2, 3, 5, 8, 10, 10]


def test_unsorted_stream_raises():
    """Passing an unsorted stream must raise a ValueError."""
    with pytest.raises(ValueError):
        combine_requests([3, 1], [2, 4])
