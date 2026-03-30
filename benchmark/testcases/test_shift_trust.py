import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_trust import shift_trust
else:
    from programs.shift_trust import shift_trust


class TestNormalization:
    """Tests that verify the output is renormalized to sum to 1.0."""

    def test_sum_to_one_equal_weights(self):
        """Output allocations should sum to 1.0 when current and target are equal uniform weights."""
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.25, 0.25, 0.25, 0.25]
        result = shift_trust(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_sum_to_one_different_weights(self):
        """Output allocations should sum to 1.0 when shifting between different distributions."""
        current = [0.6, 0.3, 0.1]
        target = [0.2, 0.5, 0.3]
        result = shift_trust(current, target, damping=0.3)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_sum_to_one_damping_one(self):
        """Output allocations should sum to 1.0 when damping=1.0 (jump to target)."""
        current = [0.5, 0.5]
        target = [0.8, 0.2]
        result = shift_trust(current, target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalized_values_with_non_unit_sum_inputs(self):
        """Output should be renormalized even when inputs don't sum to 1.0."""
        current = [1.0, 2.0, 3.0]
        target = [3.0, 2.0, 1.0]
        result = shift_trust(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_individual_values_normalized(self):
        """Each output value should be the blended value divided by the total of all blended values."""
        current = [0.7, 0.3]
        target = [0.3, 0.7]
        result = shift_trust(current, target, damping=0.5)
        # Blended: [0.7 + (0.3-0.7)*0.5, 0.3 + (0.7-0.3)*0.5] = [0.5, 0.5]
        # Normalized: [0.5, 0.5]
        assert abs(result[0] - 0.5) < 1e-9
        assert abs(result[1] - 0.5) < 1e-9


class TestBlendingBehavior:
    """Tests for correct blending and normalization behavior."""

    def test_damping_zero_preserves_current(self):
        """With damping=0, the output should equal the current allocation (normalized)."""
        current = [0.5, 0.5]
        target = [1.0, 0.0]
        result = shift_trust(current, target, damping=0.0)
        # Blended stays at current [0.5, 0.5], normalized to [0.5, 0.5]
        assert abs(result[0] - 0.5) < 1e-9
        assert abs(result[1] - 0.5) < 1e-9

    def test_damping_one_jumps_to_target(self):
        """With damping=1, output should match the target allocation (normalized)."""
        current = [0.5, 0.5]
        target = [0.8, 0.2]
        result = shift_trust(current, target, damping=1.0)
        assert abs(result[0] - 0.8) < 1e-9
        assert abs(result[1] - 0.2) < 1e-9

    def test_three_element_partial_shift_normalized(self):
        """A partial shift with three elements should produce properly normalized results."""
        current = [0.5, 0.3, 0.2]
        target = [0.1, 0.1, 0.8]
        result = shift_trust(current, target, damping=0.5)
        # Blended: [0.3, 0.2, 0.5] -> sum=1.0, normalized: [0.3, 0.2, 0.5]
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[0] - 0.3) < 1e-9
        assert abs(result[1] - 0.2) < 1e-9
        assert abs(result[2] - 0.5) < 1e-9

    def test_large_unnormalized_inputs_get_renormalized(self):
        """When inputs sum to much more than 1.0, the output must still sum to 1.0."""
        current = [10.0, 20.0, 30.0]
        target = [30.0, 20.0, 10.0]
        result = shift_trust(current, target, damping=0.5)
        # Blended: [20, 20, 20], sum=60, normalized: [1/3, 1/3, 1/3]
        assert abs(sum(result) - 1.0) < 1e-9
        for v in result:
            assert abs(v - 1.0 / 3.0) < 1e-9


class TestValidation:
    """Tests that pass on both buggy and correct versions (validation logic)."""

    def test_mismatched_lengths_raises(self):
        """Should raise ValueError when current and target have different lengths."""
        with pytest.raises(ValueError, match="shape mismatch"):
            shift_trust([0.5, 0.5], [1.0])

    def test_empty_allocation_raises(self):
        """Should raise ValueError when allocations are empty."""
        with pytest.raises(ValueError):
            shift_trust([], [])

    def test_damping_out_of_range_raises(self):
        """Should raise ValueError when damping is outside [0, 1]."""
        with pytest.raises(ValueError):
            shift_trust([0.5, 0.5], [0.5, 0.5], damping=1.5)