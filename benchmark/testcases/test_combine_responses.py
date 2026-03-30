import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.combine_responses import combine_responses
else:
    from programs.combine_responses import combine_responses


def test_empty_inputs_return_empty():
    """Merging two empty response lists yields an empty result."""
    assert combine_responses([], []) == []


def test_left_empty_returns_right():
    """When the left sequence is empty, the result equals the right sequence."""
    assert combine_responses([], [1, 3, 5]) == [1, 3, 5]


def test_right_empty_returns_left():
    """When the right sequence is empty, the result equals the left sequence."""
    assert combine_responses([2, 4, 6], []) == [2, 4, 6]


def test_disjoint_ranges_merge_correctly():
    """Non-overlapping response ranges should concatenate in sorted order."""
    result = combine_responses([1, 2, 3], [4, 5, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_interleaved_sequences():
    """Interleaved timestamps should be woven together in sorted order."""
    result = combine_responses([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_shared_tail_value_preserves_all_elements():
    """When both sequences end with the same value, all occurrences must appear."""
    result = combine_responses([1, 3, 5], [2, 4, 5])
    assert result == [1, 2, 3, 4, 5, 5]


def test_identical_sequences_double_elements():
    """Merging two identical sequences should produce every element twice."""
    result = combine_responses([1, 2, 3], [1, 2, 3])
    assert result == [1, 1, 2, 2, 3, 3]


def test_single_shared_element():
    """Two single-element sequences with the same value produce a pair."""
    result = combine_responses([7], [7])
    assert result == [7, 7]


def test_all_duplicates_at_tail():
    """Multiple duplicate tail values across inputs must all be retained."""
    result = combine_responses([5, 5, 5], [5, 5, 5])
    assert result == [5, 5, 5, 5, 5, 5]


def test_unsorted_input_raises_value_error():
    """Providing an unsorted left sequence must raise a validation error."""
    with pytest.raises(ValueError):
        combine_responses([3, 1, 2], [1, 2, 3])
