import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.latencies_merge import latencies_merge
else:
    from programs.latencies_merge import latencies_merge


def test_merge_disjoint_non_overlapping_streams():
    """Merging two streams with no common values yields the union in sorted order."""
    left = [1.0, 3.0, 5.0]
    right = [2.0, 4.0, 6.0]
    result = latencies_merge(left, right)
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_merge_empty_left_stream():
    """An empty left stream should return a copy of the right stream."""
    result = latencies_merge([], [10.0, 20.0, 30.0])
    assert result == [10.0, 20.0, 30.0]


def test_merge_empty_right_stream():
    """An empty right stream should return a copy of the left stream."""
    result = latencies_merge([5.0, 15.0], [])
    assert result == [5.0, 15.0]


def test_merge_both_empty_streams():
    """Merging two empty streams produces an empty result."""
    result = latencies_merge([], [])
    assert result == []


def test_merge_single_element_streams_different_values():
    """Single-element streams with distinct values merge correctly."""
    result = latencies_merge([100.0], [50.0])
    assert result == [50.0, 100.0]


def test_merge_preserves_duplicates_across_streams():
    """When both streams contain the same latency value, both observations must be preserved."""
    left = [5.0, 10.0, 15.0]
    right = [10.0, 20.0]
    result = latencies_merge(left, right)
    assert result == [5.0, 10.0, 10.0, 15.0, 20.0]


def test_merge_identical_single_element_streams():
    """Two single-element streams with the same value should produce two copies."""
    result = latencies_merge([7.0], [7.0])
    assert result == [7.0, 7.0]


def test_merge_preserves_all_when_last_elements_match():
    """All observations are retained even when the final elements of both streams coincide."""
    left = [1.0, 3.0, 5.0]
    right = [2.0, 4.0, 5.0]
    result = latencies_merge(left, right)
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 5.0]


def test_merge_fully_identical_streams():
    """Merging two identical streams must produce every element twice for accurate percentiles."""
    stream = [10.0, 20.0, 30.0]
    result = latencies_merge(stream, stream)
    assert result == [10.0, 10.0, 20.0, 20.0, 30.0, 30.0]


def test_merge_result_length_equals_sum_of_inputs():
    """The merged stream length must equal the total number of observations from both sources."""
    left = [1.0, 2.0, 3.0, 3.0]
    right = [3.0, 4.0, 5.0]
    result = latencies_merge(left, right)
    assert len(result) == len(left) + len(right)
