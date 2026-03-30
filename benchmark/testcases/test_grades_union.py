import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.grades_union import grades_union
else:
    from programs.grades_union import grades_union


def test_disjoint_streams():
    """Two non-overlapping grade sequences should be fully interleaved."""
    result = grades_union([10, 20, 30], [40, 50, 60])
    assert result == [10, 20, 30, 40, 50, 60]


def test_empty_left_stream():
    """An empty left stream should return all grades from the right."""
    result = grades_union([], [5, 15, 25])
    assert result == [5, 15, 25]


def test_empty_right_stream():
    """An empty right stream should return all grades from the left."""
    result = grades_union([5, 15, 25], [])
    assert result == [5, 15, 25]


def test_both_empty():
    """Two empty streams should produce an empty result."""
    result = grades_union([], [])
    assert result == []


def test_interleaved_no_overlap():
    """Alternating values from each stream should merge correctly."""
    result = grades_union([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_common_last_element_preserved():
    """When both streams share the same final grade, both copies must appear."""
    result = grades_union([10, 50], [20, 50])
    assert result == [10, 20, 50, 50]


def test_all_elements_identical():
    """Streams with the same repeated value should keep all copies."""
    result = grades_union([70, 70], [70, 70])
    assert result == [70, 70, 70, 70]


def test_single_common_element():
    """Two single-element streams with the same value should yield both."""
    result = grades_union([85], [85])
    assert result == [85, 85]


def test_shared_tail_grade_count():
    """The merged length must equal sum of both input lengths when all entries are valid."""
    left = [30, 60, 90]
    right = [45, 75, 90]
    result = grades_union(left, right)
    assert len(result) == len(left) + len(right)


def test_multiple_common_values():
    """Streams sharing several values should retain every occurrence from both."""
    result = grades_union([10, 20, 30], [10, 20, 30])
    assert result == [10, 10, 20, 20, 30, 30]
