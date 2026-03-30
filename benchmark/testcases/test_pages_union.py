import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.pages_union import pages_union
else:
    from programs.pages_union import pages_union


class TestPagesUnionBasicBehavior:
    """Tests that pass on both buggy and correct versions."""

    def test_disjoint_streams(self):
        """Union of disjoint sorted streams produces a merged sorted list."""
        result = pages_union([1, 3, 5], [2, 4, 6])
        assert result == [1, 2, 3, 4, 5, 6]

    def test_empty_left_stream(self):
        """Union with an empty left stream returns the right stream."""
        result = pages_union([], [1, 2, 3])
        assert result == [1, 2, 3]

    def test_empty_right_stream(self):
        """Union with an empty right stream returns the left stream."""
        result = pages_union([1, 2, 3], [])
        assert result == [1, 2, 3]

    def test_both_empty_streams(self):
        """Union of two empty streams returns an empty list."""
        result = pages_union([], [])
        assert result == []


class TestPagesUnionDuplicateHandling:
    """Tests targeting the duplicate-at-end boundary condition."""

    def test_single_shared_element(self):
        """Union of two streams each containing only the same single element preserves both copies."""
        result = pages_union([5], [5])
        assert result == [5, 5]

    def test_shared_last_element(self):
        """When both streams share the same last element, both copies appear in the result."""
        result = pages_union([1, 3, 7], [2, 5, 7])
        assert result == [1, 2, 3, 5, 7, 7]

    def test_multiple_shared_elements_including_last(self):
        """When streams share multiple elements including the last, all duplicates are preserved."""
        result = pages_union([1, 3, 5, 10], [2, 3, 5, 10])
        assert result == [1, 2, 3, 3, 5, 5, 10, 10]

    def test_identical_streams(self):
        """Union of two identical streams produces every element twice."""
        result = pages_union([1, 2, 3], [1, 2, 3])
        assert result == [1, 1, 2, 2, 3, 3]

    def test_shared_last_element_length_preserved(self):
        """The length of the union equals the sum of both input lengths when duplicates are kept."""
        left = [0, 5, 100]
        right = [3, 50, 100]
        result = pages_union(left, right)
        assert len(result) == len(left) + len(right)

    def test_shared_only_last_element_zero(self):
        """When the only shared element is 0 at the end (and beginning), both copies appear."""
        result = pages_union([0], [0])
        assert result == [0, 0]