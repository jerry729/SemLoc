import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.adjust_supply import adjust_supply
else:
    from programs.adjust_supply import adjust_supply


class TestNormalization:
    """Tests that verify the output is normalised to sum to 1.0."""

    def test_output_sums_to_one_equal_weights(self):
        """Output weights should sum to 1.0 when current and target are equal uniform distributions."""
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.25, 0.25, 0.25, 0.25]
        result = adjust_supply(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_different_distributions(self):
        """Output weights should sum to 1.0 when blending between different distributions."""
        current = [0.1, 0.2, 0.3, 0.4]
        target = [0.4, 0.3, 0.2, 0.1]
        result = adjust_supply(current, target, damping=0.7)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_single_element(self):
        """A single-element allocation should normalise to [1.0]."""
        current = [0.5]
        target = [0.8]
        result = adjust_supply(current, target, damping=0.5)
        assert abs(result[0] - 1.0) < 1e-9

    def test_output_sums_to_one_damping_one(self):
        """With damping=1.0 the output should equal the target distribution, normalised to sum to 1.0."""
        current = [0.1, 0.9]
        target = [0.6, 0.4]
        result = adjust_supply(current, target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[0] - 0.6) < 1e-9
        assert abs(result[1] - 0.4) < 1e-9

    def test_normalised_proportions_two_elements(self):
        """Each output weight should reflect the correct normalised proportion after blending."""
        current = [0.5, 0.5]
        target = [0.8, 0.2]
        result = adjust_supply(current, target, damping=0.5)
        # blended: [0.5 + 0.3*0.5, 0.5 + (-0.3)*0.5] = [0.65, 0.35]
        # total = 1.0, so normalised = [0.65, 0.35]
        assert abs(result[0] - 0.65) < 1e-9
        assert abs(result[1] - 0.35) < 1e-9
        assert abs(sum(result) - 1.0) < 1e-9


class TestBaselineBehavior:
    """Tests that pass on both buggy and correct versions (validation, basic structure)."""

    def test_mismatched_lengths_raises(self):
        """Should raise ValueError when current and target have different lengths."""
        with pytest.raises(ValueError, match="shape mismatch"):
            adjust_supply([0.5, 0.5], [0.3, 0.3, 0.4])

    def test_empty_allocation_raises(self):
        """Should raise ValueError when given empty sequences."""
        with pytest.raises(ValueError, match="empty allocation"):
            adjust_supply([], [])

    def test_invalid_damping_raises(self):
        """Should raise ValueError when damping is out of valid range."""
        with pytest.raises(ValueError):
            adjust_supply([0.5, 0.5], [0.5, 0.5], damping=0.0)

    def test_returns_list_of_correct_length(self):
        """Output should be a list with the same number of elements as input."""
        current = [0.2, 0.3, 0.5]
        target = [0.4, 0.4, 0.2]
        result = adjust_supply(current, target)
        assert isinstance(result, list)
        assert len(result) == 3


class TestNormalizationEdgeCases:
    """Tests for normalization with non-unit-sum inputs."""

    def test_non_unit_sum_inputs_still_normalised(self):
        """When input weights don't sum to 1.0, the output should still be normalised to sum to 1.0."""
        current = [1.0, 2.0, 3.0]
        target = [3.0, 2.0, 1.0]
        result = adjust_supply(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_large_values_normalised(self):
        """Even with large input values, output should sum to 1.0 after normalisation."""
        current = [100.0, 200.0]
        target = [300.0, 100.0]
        result = adjust_supply(current, target, damping=0.3)
        assert abs(sum(result) - 1.0) < 1e-9