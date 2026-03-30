import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.histogram_bucket_merge import histogram_bucket_merge
else:
    from programs.histogram_bucket_merge import histogram_bucket_merge


def test_disjoint_ranges():
    """Merging two non-overlapping edge lists produces a fully sorted union."""
    result = histogram_bucket_merge([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_interleaved_edges():
    """Interleaved edge values should appear in sorted order."""
    result = histogram_bucket_merge([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_empty_left():
    """An empty left histogram yields only the right edges."""
    result = histogram_bucket_merge([], [1.0, 2.0])
    assert result == [1.0, 2.0]


def test_empty_right():
    """An empty right histogram yields only the left edges."""
    result = histogram_bucket_merge([1.0, 2.0], [])
    assert result == [1.0, 2.0]


def test_both_empty():
    """Merging two empty edge lists produces an empty result."""
    result = histogram_bucket_merge([], [])
    assert result == []


def test_identical_edges_preserve_both_copies():
    """When both histograms share the same edge, both copies must be retained."""
    result = histogram_bucket_merge([5.0], [5.0])
    assert result == [5.0, 5.0]


def test_shared_terminal_edge_retained():
    """The final shared edge should still appear twice in the merged result."""
    result = histogram_bucket_merge([1.0, 3.0, 10.0], [2.0, 5.0, 10.0])
    assert result == [1.0, 2.0, 3.0, 5.0, 10.0, 10.0]


def test_all_equal_edges():
    """Histograms with identical edge lists should produce twice the edges."""
    result = histogram_bucket_merge([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert result == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]


def test_shared_last_edge_count():
    """Total element count must equal len(left) + len(right) when edges overlap at the end."""
    left = [0.0, 5.0, 10.0]
    right = [3.0, 7.0, 10.0]
    result = histogram_bucket_merge(left, right)
    assert len(result) == len(left) + len(right)


def test_unsorted_input_raises():
    """Non-sorted input must be rejected with a ValueError."""
    with pytest.raises(ValueError):
        histogram_bucket_merge([3.0, 1.0], [2.0, 4.0])
