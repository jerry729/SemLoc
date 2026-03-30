import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.timestamps_stream import timestamps_stream
else:
    from programs.timestamps_stream import timestamps_stream


def test_merge_disjoint_ranges():
    """Two non-overlapping timestamp ranges should concatenate in order."""
    result = timestamps_stream([1, 2, 3], [4, 5, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_interleaved_timestamps():
    """Interleaved timestamps should appear in sorted order after merge."""
    result = timestamps_stream([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_both_empty():
    """Merging two empty streams should produce an empty result."""
    result = timestamps_stream([], [])
    assert result == []


def test_merge_left_empty():
    """An empty left stream should return the right stream unchanged."""
    result = timestamps_stream([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_merge_right_empty():
    """An empty right stream should return the left stream unchanged."""
    result = timestamps_stream([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_merge_preserves_total_element_count_with_shared_tail():
    """Merged output must contain every element from both inputs."""
    left = [1, 3, 5]
    right = [2, 4, 5]
    result = timestamps_stream(left, right)
    assert len(result) == len(left) + len(right)


def test_merge_identical_streams():
    """Merging two identical streams should produce all elements from both."""
    stream = [10, 20, 30]
    result = timestamps_stream(stream, stream)
    assert result == [10, 10, 20, 20, 30, 30]


def test_merge_single_common_element():
    """When both streams share only a final element, all values must be kept."""
    result = timestamps_stream([5], [5])
    assert result == [5, 5]


def test_merge_preserves_duplicates_at_end():
    """Duplicate timestamps at the tail of both inputs must all be retained."""
    left = [1, 2, 7]
    right = [3, 4, 7]
    result = timestamps_stream(left, right)
    assert result == [1, 2, 3, 4, 7, 7]


def test_unsorted_input_raises():
    """Providing an unsorted sequence should raise a ValueError."""
    with pytest.raises(ValueError):
        timestamps_stream([3, 1, 2], [4, 5])
