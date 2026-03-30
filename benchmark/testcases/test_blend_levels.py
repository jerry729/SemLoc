import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.blend_levels import blend_levels
else:
    from programs.blend_levels import blend_levels


def test_empty_inputs_produce_empty_result():
    """Merging two empty ladders must yield an empty ladder."""
    assert blend_levels([], []) == []


def test_left_empty_returns_right():
    """When left is empty the result equals the right ladder."""
    assert blend_levels([], [1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]


def test_right_empty_returns_left():
    """When right is empty the result equals the left ladder."""
    assert blend_levels([10.0, 20.0], []) == [10.0, 20.0]


def test_interleaved_levels_sorted():
    """Interleaved price levels must appear in non-decreasing order."""
    result = blend_levels([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_identical_single_element_preserved():
    """Two single-element ladders with the same price should both appear."""
    result = blend_levels([5.0], [5.0])
    assert result == [5.0, 5.0]


def test_all_duplicate_levels_preserved():
    """When both ladders are identical every element must appear twice."""
    result = blend_levels([1, 2, 3], [1, 2, 3])
    assert result == [1, 1, 2, 2, 3, 3]


def test_shared_tail_value_not_removed():
    """All elements should be kept even when the last values coincide."""
    result = blend_levels([2, 5], [3, 5])
    assert result == [2, 3, 5, 5]


def test_longer_left_with_shared_max():
    """The total element count must equal the sum of both input lengths."""
    left = [1, 4, 7, 10]
    right = [2, 6, 10]
    result = blend_levels(left, right)
    assert len(result) == len(left) + len(right)
    assert result == [1, 2, 4, 6, 7, 10, 10]


def test_unsorted_input_raises():
    """An unsorted input ladder must cause a ValueError."""
    with pytest.raises(ValueError):
        blend_levels([5, 3, 1], [1, 2, 3])


def test_triple_shared_tail_preserves_count():
    """Multiple shared trailing values across both inputs are all retained."""
    left = [1, 5, 5]
    right = [2, 5, 5]
    result = blend_levels(left, right)
    assert result == [1, 2, 5, 5, 5, 5]
