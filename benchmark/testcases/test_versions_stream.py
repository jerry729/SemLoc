import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.versions_stream import versions_stream
else:
    from programs.versions_stream import versions_stream


def test_disjoint_streams_interleave_correctly():
    """Two non-overlapping streams should produce a fully interleaved result."""
    left = ["1.0.0", "3.0.0", "5.0.0"]
    right = ["2.0.0", "4.0.0", "6.0.0"]
    result = versions_stream(left, right)
    assert result == ["1.0.0", "2.0.0", "3.0.0", "4.0.0", "5.0.0", "6.0.0"]


def test_empty_left_stream():
    """An empty left stream should return a copy of the right stream."""
    result = versions_stream([], ["1.0.0", "2.0.0"])
    assert result == ["1.0.0", "2.0.0"]


def test_empty_right_stream():
    """An empty right stream should return a copy of the left stream."""
    result = versions_stream(["1.0.0", "2.0.0"], [])
    assert result == ["1.0.0", "2.0.0"]


def test_both_empty_streams():
    """Two empty streams should produce an empty result."""
    assert versions_stream([], []) == []


def test_left_fully_before_right():
    """When all left versions precede right versions, left appears first."""
    left = ["0.1.0", "0.2.0"]
    right = ["1.0.0", "2.0.0"]
    result = versions_stream(left, right)
    assert result == ["0.1.0", "0.2.0", "1.0.0", "2.0.0"]


def test_duplicate_versions_both_retained():
    """When the same version appears in both streams, both copies must appear in the output."""
    left = ["1.0.0", "2.0.0"]
    right = ["2.0.0", "3.0.0"]
    result = versions_stream(left, right)
    assert result.count("2.0.0") == 2


def test_identical_single_element_streams():
    """Two single-element streams with the same version should yield two entries."""
    result = versions_stream(["5.0.0"], ["5.0.0"])
    assert result == ["5.0.0", "5.0.0"]


def test_identical_streams_preserve_all_copies():
    """Merging two identical multi-element streams should keep every version twice."""
    stream = ["1.0.0", "2.0.0", "3.0.0"]
    result = versions_stream(stream, stream)
    assert len(result) == 6
    assert result == ["1.0.0", "1.0.0", "2.0.0", "2.0.0", "3.0.0", "3.0.0"]


def test_shared_tail_version_not_dropped():
    """When both streams end with the same version, the merged stream must contain both copies."""
    left = ["1.0.0", "4.0.0"]
    right = ["2.0.0", "4.0.0"]
    result = versions_stream(left, right)
    assert result == ["1.0.0", "2.0.0", "4.0.0", "4.0.0"]


def test_total_length_equals_sum_of_inputs():
    """The merged stream length must always equal the sum of both input lengths."""
    left = ["a", "c", "e", "g"]
    right = ["b", "d", "e", "f"]
    result = versions_stream(left, right)
    assert len(result) == len(left) + len(right)
