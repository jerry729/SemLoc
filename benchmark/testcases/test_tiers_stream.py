import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.tiers_stream import tiers_stream
else:
    from programs.tiers_stream import tiers_stream


def test_merge_disjoint_ranges():
    """Merging two non-overlapping sorted sequences produces the full sorted result."""
    result = tiers_stream([1, 2, 3], [4, 5, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_empty_left():
    """An empty left stream yields the right stream unchanged."""
    result = tiers_stream([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_merge_empty_right():
    """An empty right stream yields the left stream unchanged."""
    result = tiers_stream([5, 15, 25], [])
    assert result == [5, 15, 25]


def test_merge_both_empty():
    """Merging two empty streams produces an empty result."""
    result = tiers_stream([], [])
    assert result == []


def test_merge_interleaved_elements():
    """Interleaved tier values should appear in globally sorted order."""
    result = tiers_stream([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_with_shared_last_element():
    """When both streams end with the same tier value, all elements must be retained."""
    result = tiers_stream([1, 3, 5], [2, 4, 5])
    assert result == [1, 2, 3, 4, 5, 5]


def test_merge_identical_sequences():
    """Merging two identical sequences should double every element in sorted order."""
    result = tiers_stream([1, 2, 3], [1, 2, 3])
    assert result == [1, 1, 2, 2, 3, 3]


def test_merge_all_equal_elements():
    """Merging streams where every element is the same should concatenate them fully."""
    result = tiers_stream([7, 7, 7], [7, 7])
    assert result == [7, 7, 7, 7, 7]


def test_total_element_count_preserved():
    """The merged result must contain exactly len(left) + len(right) elements."""
    left = [10, 20, 50]
    right = [30, 40, 50]
    result = tiers_stream(left, right)
    assert len(result) == len(left) + len(right)


def test_merge_single_shared_element():
    """Merging single-element lists with the same value should yield both copies."""
    result = tiers_stream([42], [42])
    assert result == [42, 42]
