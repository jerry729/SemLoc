import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.demands_union import demands_union
else:
    from programs.demands_union import demands_union


def test_merge_disjoint_ascending_ranges():
    """Two non-overlapping sorted ranges should produce a fully sorted union."""
    result = demands_union([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_empty_left_list():
    """An empty left list should return the right list unchanged."""
    result = demands_union([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_merge_empty_right_list():
    """An empty right list should return the left list unchanged."""
    result = demands_union([5, 15, 25], [])
    assert result == [5, 15, 25]


def test_merge_both_empty():
    """Merging two empty demand lists should yield an empty result."""
    result = demands_union([], [])
    assert result == []


def test_merge_single_element_lists():
    """Single-element lists with distinct values should merge correctly."""
    result = demands_union([1], [2])
    assert result == [1, 2]


def test_merge_with_shared_last_element():
    """When both lists share the same last element, all elements must be preserved."""
    result = demands_union([1, 3, 5], [2, 4, 5])
    assert result == [1, 2, 3, 4, 5, 5]


def test_merge_identical_lists():
    """Merging two identical demand lists should produce every element twice."""
    result = demands_union([1, 2, 3], [1, 2, 3])
    assert result == [1, 1, 2, 2, 3, 3]


def test_result_length_equals_sum_of_inputs():
    """The merged list length must equal the sum of both input lengths."""
    left = [1, 5, 9, 9]
    right = [2, 5, 9]
    result = demands_union(left, right)
    assert len(result) == len(left) + len(right)


def test_merge_preserves_duplicates_at_boundary():
    """Duplicate values at the end of both lists must all appear in the output."""
    result = demands_union([3, 7], [5, 7])
    assert result == [3, 5, 7, 7]


def test_negative_values_rejected():
    """Demand values below the configured floor should raise ValueError."""
    with pytest.raises(ValueError):
        demands_union([-1, 2], [3, 4])
