import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.ids_merge import ids_merge
else:
    from programs.ids_merge import ids_merge


def test_empty_inputs():
    """Merging two empty sequences produces an empty result."""
    assert ids_merge([], []) == []


def test_left_empty():
    """When the left sequence is empty, the result equals the right sequence."""
    assert ids_merge([], [1, 3, 5]) == [1, 3, 5]


def test_right_empty():
    """When the right sequence is empty, the result equals the left sequence."""
    assert ids_merge([2, 4, 6], []) == [2, 4, 6]


def test_interleaved_disjoint_ids():
    """Disjoint sorted sequences should interleave correctly."""
    assert ids_merge([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]


def test_single_element_each():
    """Two single-element sequences merge into a two-element sorted list."""
    assert ids_merge([1], [2]) == [1, 2]


def test_shared_last_element():
    """When both sequences end with the same ID, both occurrences must appear in the output."""
    result = ids_merge([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_all_duplicates_shared_tail():
    """Merging identical sequences must produce every element from both."""
    result = ids_merge([2, 4, 6], [2, 4, 6])
    assert result == [2, 2, 4, 4, 6, 6]


def test_output_length_equals_sum_of_inputs():
    """The merged list length must equal the sum of both input lengths."""
    left = [10, 20, 30]
    right = [15, 25, 30]
    result = ids_merge(left, right)
    assert len(result) == len(left) + len(right)


def test_multiple_trailing_duplicates():
    """Multiple shared trailing values should all be preserved."""
    result = ids_merge([1, 7, 7], [3, 7])
    assert result == [1, 3, 7, 7, 7]


def test_unsorted_input_raises():
    """Providing an unsorted left sequence must raise a ValueError."""
    with pytest.raises(ValueError):
        ids_merge([3, 1, 2], [1, 2, 3])
