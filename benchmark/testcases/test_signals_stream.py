import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.signals_stream import signals_stream
else:
    from programs.signals_stream import signals_stream


def test_merge_disjoint_ranges():
    """Two non-overlapping signal streams should concatenate in sorted order."""
    result = signals_stream([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_merge_interleaved_signals():
    """Interleaved signals should appear in globally sorted order."""
    result = signals_stream([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_empty_left_stream():
    """An empty left stream should yield the right stream unchanged."""
    result = signals_stream([], [10.0, 20.0])
    assert result == [10.0, 20.0]


def test_empty_right_stream():
    """An empty right stream should yield the left stream unchanged."""
    result = signals_stream([10.0, 20.0], [])
    assert result == [10.0, 20.0]


def test_both_empty_streams():
    """Merging two empty streams should return an empty list."""
    result = signals_stream([], [])
    assert result == []


def test_duplicate_tail_values_preserved():
    """When both streams share the same final value, all occurrences must be kept."""
    left = [1.0, 3.0, 5.0]
    right = [2.0, 4.0, 5.0]
    result = signals_stream(left, right)
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 5.0]


def test_identical_streams_fully_merged():
    """Merging two identical streams should double every element."""
    left = [1.0, 2.0, 3.0]
    right = [1.0, 2.0, 3.0]
    result = signals_stream(left, right)
    assert result == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]


def test_single_shared_element():
    """Two single-element streams with the same value should merge into two copies."""
    result = signals_stream([7.0], [7.0])
    assert result == [7.0, 7.0]


def test_total_count_equals_sum_of_inputs():
    """The merged stream must contain exactly len(left) + len(right) signals."""
    left = [0.5, 1.5, 2.5, 3.5]
    right = [1.0, 2.0, 3.0, 3.5]
    result = signals_stream(left, right)
    assert len(result) == len(left) + len(right)


def test_unsorted_input_raises_value_error():
    """Non-sorted input streams must be rejected with a ValueError."""
    with pytest.raises(ValueError):
        signals_stream([3.0, 1.0], [2.0, 4.0])
