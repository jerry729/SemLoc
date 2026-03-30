import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.dataloader_shard_merge import dataloader_shard_merge
else:
    from programs.dataloader_shard_merge import dataloader_shard_merge


def test_merge_disjoint_ranges():
    """Merging two non-overlapping shard ranges produces a fully sorted union."""
    result = dataloader_shard_merge([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_merge_empty_left():
    """An empty left list yields the right list unchanged."""
    result = dataloader_shard_merge([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_merge_empty_right():
    """An empty right list yields the left list unchanged."""
    result = dataloader_shard_merge([10, 20, 30], [])
    assert result == [10, 20, 30]


def test_merge_both_empty():
    """Merging two empty shard lists produces an empty result."""
    result = dataloader_shard_merge([], [])
    assert result == []


def test_merge_preserves_duplicates_across_lists():
    """Duplicate shard IDs appearing in both inputs must both appear in the output."""
    result = dataloader_shard_merge([1, 2, 3], [2, 3, 4])
    assert result == [1, 2, 2, 3, 3, 4]


def test_merge_identical_single_element():
    """Two single-element lists with the same shard ID produce two copies."""
    result = dataloader_shard_merge([5], [5])
    assert result == [5, 5]


def test_merge_shared_tail_preserves_all():
    """When both lists end with the same ID, all elements must be retained."""
    result = dataloader_shard_merge([1, 3, 7], [2, 5, 7])
    assert result == [1, 2, 3, 5, 7, 7]


def test_merge_all_same_values():
    """Lists consisting entirely of one repeated value produce the full concatenation."""
    result = dataloader_shard_merge([4, 4, 4], [4, 4])
    assert result == [4, 4, 4, 4, 4]


def test_merge_with_stride_filtering():
    """Stride > 1 should thin the merged output to every stride-th element."""
    result = dataloader_shard_merge([1, 3, 5], [2, 4, 6], stride=2)
    assert result == [1, 3, 5]


def test_merge_raises_on_unsorted_input():
    """Unsorted shard ID sequences must be rejected with a clear error."""
    with pytest.raises(ValueError):
        dataloader_shard_merge([5, 3, 1], [2, 4, 6])
