import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.weights_union import weights_union
else:
    from programs.weights_union import weights_union


def test_disjoint_streams_no_overlap():
    """Two streams with no shared values should produce a simple merge."""
    result = weights_union([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_empty_left_stream():
    """An empty left stream returns a copy of the right stream."""
    result = weights_union([], [1.0, 2.0, 3.0])
    assert result == [1.0, 2.0, 3.0]


def test_empty_right_stream():
    """An empty right stream returns a copy of the left stream."""
    result = weights_union([1.0, 2.0, 3.0], [])
    assert result == [1.0, 2.0, 3.0]


def test_both_empty_streams():
    """Two empty streams should produce an empty result."""
    result = weights_union([], [])
    assert result == []


def test_single_shared_element_in_middle():
    """A shared element that is not the last should appear twice in the merged output."""
    result = weights_union([1.0, 3.0, 5.0], [2.0, 3.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 3.0, 5.0, 6.0]


def test_identical_single_element_streams():
    """Two single-element streams with the same value should produce both copies."""
    result = weights_union([5.0], [5.0])
    assert result == [5.0, 5.0]


def test_shared_last_element_preserved():
    """When both streams end with the same value, both copies must be in the output."""
    result = weights_union([1.0, 4.0], [2.0, 4.0])
    assert result == [1.0, 2.0, 4.0, 4.0]


def test_fully_overlapping_streams():
    """Two identical streams should produce every element twice."""
    result = weights_union([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert result == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]


def test_shared_tail_with_longer_left():
    """Both streams sharing only the last element must retain both occurrences."""
    result = weights_union([1.0, 2.0, 5.0], [5.0])
    assert result == [1.0, 2.0, 5.0, 5.0]


def test_unsorted_stream_raises_error():
    """An unsorted input stream should raise a ValueError."""
    with pytest.raises(ValueError):
        weights_union([3.0, 1.0], [2.0, 4.0])
