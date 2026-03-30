import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.blend_supplies import blend_supplies
else:
    from programs.blend_supplies import blend_supplies


def test_disjoint_ranges():
    """Non-overlapping supply manifests should concatenate in sorted order."""
    result = blend_supplies([1, 3, 5], [2, 4, 6])
    assert result == [1, 2, 3, 4, 5, 6]


def test_left_empty():
    """An empty left manifest should yield the right manifest unchanged."""
    result = blend_supplies([], [10, 20, 30])
    assert result == [10, 20, 30]


def test_right_empty():
    """An empty right manifest should yield the left manifest unchanged."""
    result = blend_supplies([5, 15, 25], [])
    assert result == [5, 15, 25]


def test_both_empty():
    """Blending two empty manifests produces an empty list."""
    result = blend_supplies([], [])
    assert result == []


def test_single_element_each_no_overlap():
    """Single-element manifests with distinct values merge correctly."""
    result = blend_supplies([1], [2])
    assert result == [1, 2]


def test_shared_last_element_both_lists():
    """When both manifests end with the same value, all items must be retained."""
    result = blend_supplies([1, 5], [3, 5])
    assert result == [1, 3, 5, 5]


def test_identical_single_element():
    """Two single-element manifests with equal values should produce two items."""
    result = blend_supplies([7], [7])
    assert result == [7, 7]


def test_all_same_values():
    """Manifests of identical repeated values should preserve total count."""
    result = blend_supplies([3, 3, 3], [3, 3])
    assert result == [3, 3, 3, 3, 3]


def test_shared_tail_different_lengths():
    """Manifests of different lengths sharing a tail value preserve all elements."""
    result = blend_supplies([2, 4, 10], [1, 10])
    assert result == [1, 2, 4, 10, 10]


def test_negative_value_rejected():
    """Supply items below the minimum threshold must be rejected."""
    with pytest.raises(ValueError):
        blend_supplies([-1, 2], [3])
