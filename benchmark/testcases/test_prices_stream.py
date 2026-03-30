import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.prices_stream import prices_stream
else:
    from programs.prices_stream import prices_stream


def test_disjoint_ascending_streams():
    """Two streams with no overlapping prices merge into a single sorted sequence."""
    result = prices_stream([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_empty_left_stream():
    """An empty left stream returns the right stream unchanged."""
    result = prices_stream([], [1.5, 2.5, 3.5])
    assert result == [1.5, 2.5, 3.5]


def test_empty_right_stream():
    """An empty right stream returns the left stream unchanged."""
    result = prices_stream([10.0, 20.0], [])
    assert result == [10.0, 20.0]


def test_both_empty():
    """Merging two empty streams yields an empty result."""
    result = prices_stream([], [])
    assert result == []


def test_single_element_no_overlap():
    """Single-element streams with distinct values merge correctly."""
    result = prices_stream([5.0], [3.0])
    assert result == [3.0, 5.0]


def test_duplicate_prices_at_end_preserved():
    """A price present in both streams at the tail must appear twice in the output."""
    result = prices_stream([1.0, 5.0], [2.0, 5.0])
    assert result == [1.0, 2.0, 5.0, 5.0]


def test_identical_streams_preserve_all_duplicates():
    """When both streams are identical every element should appear twice."""
    result = prices_stream([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert result == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]


def test_all_same_price_preserves_count():
    """Streams that each contain the same single price must yield two copies."""
    result = prices_stream([4.0], [4.0])
    assert result == [4.0, 4.0]


def test_overlap_in_middle_only():
    """Duplicate prices in the middle (not at the tail) must both appear."""
    result = prices_stream([1.0, 3.0, 5.0], [2.0, 3.0, 6.0])
    assert result == [1.0, 2.0, 3.0, 3.0, 5.0, 6.0]


def test_multiple_trailing_duplicates():
    """When multiple trailing prices coincide the total count must equal left + right counts."""
    left = [1.0, 3.0, 5.0, 7.0]
    right = [2.0, 4.0, 6.0, 7.0]
    result = prices_stream(left, right)
    assert result.count(7.0) == 2
    assert result == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.0]
