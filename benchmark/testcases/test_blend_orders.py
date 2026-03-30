import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.blend_orders import blend_orders
else:
    from programs.blend_orders import blend_orders


def test_disjoint_non_overlapping_streams():
    """Two streams with no common values should produce a simple interleave."""
    result = blend_orders([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_empty_left_stream():
    """An empty left stream should return the right stream unchanged."""
    result = blend_orders([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_empty_right_stream():
    """An empty right stream should return the left stream unchanged."""
    result = blend_orders([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_both_empty_streams():
    """Two empty streams should produce an empty result."""
    result = blend_orders([], [])
    assert result == []


def test_single_element_each_different():
    """Single-element streams with different values merge in order."""
    result = blend_orders([5], [3])
    assert result == [3, 5]


def test_matching_last_elements_preserved():
    """When both streams share the same last value, both copies must appear in the output."""
    result = blend_orders([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_identical_streams():
    """Two identical streams should produce every element twice in sorted order."""
    result = blend_orders([2, 4, 6], [2, 4, 6])
    assert result == [2, 2, 4, 4, 6, 6]


def test_all_equal_elements():
    """Streams consisting entirely of the same value should all be preserved."""
    result = blend_orders([7, 7, 7], [7, 7])
    assert result == [7, 7, 7, 7, 7]


def test_shared_tail_value_three_elements():
    """Streams sharing only the final element should still retain both copies."""
    result = blend_orders([1, 2, 10], [5, 8, 10])
    assert result == [1, 2, 5, 8, 10, 10]


def test_unsorted_stream_raises_error():
    """An unsorted input stream should raise a ValueError during validation."""
    with pytest.raises(ValueError):
        blend_orders([3, 1, 2], [1, 2, 3])
