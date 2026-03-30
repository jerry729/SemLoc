import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.combine_depths import combine_depths
else:
    from programs.combine_depths import combine_depths


def test_disjoint_depth_streams():
    """Merging non-overlapping sorted streams produces a fully sorted union."""
    left = [1.0, 3.0, 5.0]
    right = [2.0, 4.0, 6.0]
    result = combine_depths(left, right)
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_empty_left_stream():
    """An empty left stream returns right stream unchanged."""
    result = combine_depths([], [10.0, 20.0, 30.0])
    assert result == [10.0, 20.0, 30.0]


def test_empty_right_stream():
    """An empty right stream returns left stream unchanged."""
    result = combine_depths([10.0, 20.0], [])
    assert result == [10.0, 20.0]


def test_both_empty():
    """Two empty streams produce an empty result."""
    assert combine_depths([], []) == []


def test_duplicate_interior_levels():
    """Shared price levels in the middle should both be preserved in output."""
    left = [1.0, 5.0, 10.0]
    right = [2.0, 5.0, 8.0]
    result = combine_depths(left, right)
    assert result == [1.0, 2.0, 5.0, 5.0, 8.0, 10.0]


def test_identical_single_element_streams():
    """Two single-element streams with equal values produce both entries."""
    result = combine_depths([7.0], [7.0])
    assert len(result) == 2
    assert result == [7.0, 7.0]


def test_shared_tail_level_preserved():
    """When both streams share the same final price level, both entries must appear."""
    left = [1.0, 3.0, 5.0]
    right = [2.0, 4.0, 5.0]
    result = combine_depths(left, right)
    assert result.count(5.0) == 2


def test_all_elements_identical():
    """Streams consisting entirely of the same price should preserve every entry."""
    left = [4.0, 4.0, 4.0]
    right = [4.0, 4.0]
    result = combine_depths(left, right)
    assert len(result) == 5


def test_total_count_with_shared_last():
    """Total output length equals sum of inputs when all entries are shared."""
    left = [10.0, 20.0, 30.0]
    right = [10.0, 20.0, 30.0]
    result = combine_depths(left, right)
    assert len(result) == 6


def test_unsorted_input_raises():
    """Unsorted depth streams are rejected with a ValueError."""
    with pytest.raises(ValueError):
        combine_depths([5.0, 3.0, 1.0], [1.0, 2.0])
