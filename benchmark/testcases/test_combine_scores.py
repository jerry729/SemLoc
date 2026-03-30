import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.combine_scores import combine_scores
else:
    from programs.combine_scores import combine_scores


def test_merge_disjoint_ranges():
    """Merging two non-overlapping score ranges preserves all elements in order."""
    result = combine_scores([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_merge_interleaved_scores():
    """Interleaved scores from two sources are merged into a single sorted list."""
    result = combine_scores([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_merge_empty_left():
    """Merging an empty left sequence returns the right sequence unchanged."""
    result = combine_scores([], [1.0, 2.0, 3.0])
    assert result == [1.0, 2.0, 3.0]


def test_merge_empty_right():
    """Merging an empty right sequence returns the left sequence unchanged."""
    result = combine_scores([1.0, 2.0], [])
    assert result == [1.0, 2.0]


def test_merge_both_empty():
    """Merging two empty sequences produces an empty result."""
    result = combine_scores([], [])
    assert result == []


def test_total_element_count_with_shared_tail():
    """All elements from both inputs must appear in the merged output."""
    left = [1.0, 5.0]
    right = [3.0, 5.0]
    result = combine_scores(left, right)
    assert len(result) == len(left) + len(right)


def test_duplicate_scores_preserved():
    """Duplicate scores across sources must all be retained in the merge."""
    result = combine_scores([2.0, 2.0], [2.0, 2.0])
    assert len(result) == 4
    assert all(abs(v - 2.0) < 1e-9 for v in result)


def test_identical_single_element_lists():
    """Two single-element lists with the same score yield two elements."""
    result = combine_scores([7.0], [7.0])
    assert len(result) == 2
    assert result == [7.0, 7.0]


def test_merge_preserves_length_common_maximum():
    """When both inputs share the same maximum, the merged length equals the sum."""
    left = [1.0, 3.0, 10.0]
    right = [2.0, 8.0, 10.0]
    result = combine_scores(left, right)
    assert len(result) == 6


def test_unsorted_input_raises():
    """Passing an unsorted sequence must raise a ValueError."""
    with pytest.raises(ValueError):
        combine_scores([3.0, 1.0], [2.0, 4.0])
