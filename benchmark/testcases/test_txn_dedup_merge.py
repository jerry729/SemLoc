import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.txn_dedup_merge import txn_dedup_merge
else:
    from programs.txn_dedup_merge import txn_dedup_merge


def test_disjoint_ascending_ranges():
    """Merging two non-overlapping ranges produces all elements in order."""
    result = txn_dedup_merge([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_both_empty_lists():
    """Merging two empty transaction lists yields an empty result."""
    result = txn_dedup_merge([], [])
    assert result == []


def test_left_empty():
    """Merging an empty left list with a populated right returns right unchanged."""
    result = txn_dedup_merge([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_right_empty():
    """Merging a populated left with an empty right returns left unchanged."""
    result = txn_dedup_merge([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_single_common_element_in_middle():
    """When lists share an element that is not the last, both copies appear in the merged output."""
    result = txn_dedup_merge([1, 5, 10], [3, 5, 12])
    assert result == [1, 3, 5, 5, 10, 12]


def test_identical_single_element_lists():
    """Two single-element lists with the same ID should produce two copies."""
    result = txn_dedup_merge([42], [42])
    assert result == [42, 42]


def test_common_last_element_preserved():
    """When both lists end with the same transaction ID, the merged result contains both copies."""
    result = txn_dedup_merge([1, 3, 7], [2, 5, 7])
    assert result == [1, 2, 3, 5, 7, 7]


def test_fully_overlapping_lists():
    """Merging identical lists produces each element twice, in sorted order."""
    result = txn_dedup_merge([1, 2, 3], [1, 2, 3])
    assert result == [1, 1, 2, 2, 3, 3]


def test_total_count_with_shared_tail():
    """The total number of elements in the merged result equals the sum of both inputs."""
    left = [10, 20, 50]
    right = [30, 40, 50]
    result = txn_dedup_merge(left, right)
    assert len(result) == len(left) + len(right)


def test_unsorted_input_raises():
    """Providing an unsorted transaction list must raise a ValueError."""
    with pytest.raises(ValueError):
        txn_dedup_merge([5, 3, 1], [2, 4, 6])
