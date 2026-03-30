import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.combine_offsets import combine_offsets
else:
    from programs.combine_offsets import combine_offsets


def test_empty_inputs_produce_empty_result():
    """Merging two empty offset lists yields an empty list."""
    assert combine_offsets([], []) == []


def test_left_empty_returns_right():
    """When the left list is empty, the result equals the right list."""
    assert combine_offsets([], [1, 3, 5]) == [1, 3, 5]


def test_right_empty_returns_left():
    """When the right list is empty, the result equals the left list."""
    assert combine_offsets([2, 4, 6], []) == [2, 4, 6]


def test_interleaved_offsets_sorted():
    """Interleaved offset sequences produce a fully sorted merged result."""
    result = combine_offsets([1, 5, 9], [2, 6, 10])
    assert result == [1, 2, 5, 6, 9, 10]


def test_non_overlapping_ascending():
    """Two non-overlapping ascending ranges merge into one sorted sequence."""
    result = combine_offsets([1, 2, 3], [4, 5, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_shared_last_element_preserved():
    """When both lists end with the same offset value, all elements must appear in the merge."""
    result = combine_offsets([1, 3, 5], [2, 4, 5])
    assert result == [1, 2, 3, 4, 5, 5]


def test_identical_single_element_lists():
    """Two single-element lists with the same value should produce two entries."""
    result = combine_offsets([7], [7])
    assert result == [7, 7]


def test_identical_lists_fully_duplicated():
    """Merging identical offset lists should double every entry."""
    result = combine_offsets([10, 20, 30], [10, 20, 30])
    assert result == [10, 10, 20, 20, 30, 30]


def test_shared_tail_offset_count():
    """Total element count equals sum of input lengths regardless of shared tail values."""
    left = [0, 100, 200]
    right = [50, 150, 200]
    result = combine_offsets(left, right)
    assert len(result) == len(left) + len(right)


def test_out_of_range_offset_raises():
    """Offset values below zero are rejected with a ValueError."""
    with pytest.raises(ValueError):
        combine_offsets([-1], [0])
