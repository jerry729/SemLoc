import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.stream_joiner import stream_joiner
else:
    from programs.stream_joiner import stream_joiner


def test_merge_disjoint_ranges():
    """Merging two non-overlapping sorted streams yields a fully sorted result."""
    result = stream_joiner([1, 2, 3], [4, 5, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_interleaved_ids():
    """Interleaved event ids from two sources should appear in global sorted order."""
    result = stream_joiner([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_both_empty():
    """Merging two empty streams produces an empty result."""
    result = stream_joiner([], [])
    assert result == []


def test_merge_one_empty_left():
    """An empty left stream should return all elements from the right stream."""
    result = stream_joiner([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_merge_one_empty_right():
    """An empty right stream should return all elements from the left stream."""
    result = stream_joiner([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_merge_preserves_all_duplicates_across_streams():
    """When both streams share the same trailing id, the merged result must retain all occurrences."""
    result = stream_joiner([1, 3, 5], [2, 4, 5])
    assert result == [1, 2, 3, 4, 5, 5]


def test_merge_identical_single_element_streams():
    """Two single-element streams with the same id should produce two copies in the output."""
    result = stream_joiner([7], [7])
    assert result == [7, 7]


def test_merge_total_count_preserved():
    """The total number of elements in the merged stream equals the sum of both input lengths."""
    left = [1, 5, 5, 10]
    right = [5, 10, 15]
    result = stream_joiner(left, right)
    assert len(result) == len(left) + len(right)


def test_merge_streams_with_shared_tail_value():
    """Streams ending with the same value must each contribute that value to the output."""
    result = stream_joiner([2, 4, 8], [1, 3, 8])
    assert result.count(8) == 2


def test_invalid_input_type_raises_type_error():
    """Passing a non-sequence type should raise a TypeError."""
    with pytest.raises(TypeError):
        stream_joiner("abc", [1, 2, 3])
