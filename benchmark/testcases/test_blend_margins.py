import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.blend_margins import blend_margins
else:
    from programs.blend_margins import blend_margins


def test_disjoint_non_overlapping_streams():
    """Merging two non-overlapping sorted streams yields a fully sorted union."""
    result = blend_margins([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_empty_left_stream():
    """An empty left stream returns the right stream unchanged."""
    result = blend_margins([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_empty_right_stream():
    """An empty right stream returns the left stream unchanged."""
    result = blend_margins([5, 15, 25], [])
    assert result == [5, 15, 25]


def test_both_empty():
    """Merging two empty streams produces an empty result."""
    assert blend_margins([], []) == []


def test_identical_single_element():
    """Equal single-element streams produce both copies in the output."""
    result = blend_margins([7], [7])
    assert result == [7, 7]


def test_shared_tail_value_preserves_all_copies():
    """When both streams end with the same margin value, both copies must be present."""
    result = blend_margins([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_all_equal_elements():
    """All-equal streams should yield twice as many elements as one stream."""
    left = [4, 4, 4]
    right = [4, 4, 4]
    result = blend_margins(left, right)
    assert len(result) == 6
    assert all(v == 4 for v in result)


def test_total_element_count_with_shared_last():
    """The merged result must contain every element from both input streams."""
    left = [2, 8, 10]
    right = [5, 10]
    result = blend_margins(left, right)
    assert len(result) == len(left) + len(right)


def test_multiple_trailing_duplicates():
    """Streams sharing the last two values should keep all paired copies."""
    left = [1, 3, 3]
    right = [2, 3, 3]
    result = blend_margins(left, right)
    assert result == [1, 2, 3, 3, 3, 3]


def test_unsorted_input_raises():
    """Unsorted input streams must be rejected with a ValueError."""
    with pytest.raises(ValueError):
        blend_margins([5, 3, 1], [1, 2, 3])
