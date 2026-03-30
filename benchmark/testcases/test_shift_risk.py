import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_risk import shift_risk
else:
    from programs.shift_risk import shift_risk


class TestNormalization:
    """Tests that verify the output allocation is normalized to sum to 1.0."""

    def test_output_sums_to_one_default_damping(self):
        """The returned allocation weights should sum to 1.0."""
        current = [0.5, 0.3, 0.2]
        target = [0.4, 0.4, 0.2]
        result = shift_risk(current, target)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_small_damping(self):
        """With a small damping factor, the result should still sum to 1.0."""
        current = [0.6, 0.2, 0.1, 0.1]
        target = [0.25, 0.25, 0.25, 0.25]
        result = shift_risk(current, target, damping=0.1)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_damping_one(self):
        """With damping=1.0, the result should equal the target and sum to 1.0."""
        current = [0.7, 0.2, 0.1]
        target = [0.3, 0.5, 0.2]
        result = shift_risk(current, target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalized_values_two_assets(self):
        """For two assets, normalized output should have correct individual values."""
        current = [0.8, 0.2]
        target = [0.4, 0.6]
        result = shift_risk(current, target, damping=0.5)
        # adjusted = [0.8 + (0.4-0.8)*0.5, 0.2 + (0.6-0.2)*0.5] = [0.6, 0.4]
        # sum = 1.0, so normalized = [0.6, 0.4]
        assert abs(result[0] - 0.6) < 1e-9
        assert abs(result[1] - 0.4) < 1e-9
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalization_when_sum_deviates(self):
        """When clamping causes the sum to deviate from 1.0, normalization should correct it."""
        # current and target that after interpolation and clamping won't sum to 1
        # e.g., current = [0.0, 0.0, 1.0], target = [0.0, 0.0, 0.5]
        # damping=0.5 => adjusted = [0.0, 0.0, 0.75], sum=0.75
        # After normalization: [0.0, 0.0, 1.0]
        current = [0.0, 0.0, 1.0]
        target = [0.0, 0.0, 0.5]
        result = shift_risk(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9


class TestBasicBehavior:
    """Tests for basic behavior that should pass on both versions."""

    def test_same_current_and_target(self):
        """When current equals target, the output should equal the input."""
        current = [0.5, 0.3, 0.2]
        target = [0.5, 0.3, 0.2]
        result = shift_risk(current, target)
        for r, c in zip(result, current):
            assert abs(r - c) < 1e-9

    def test_shape_mismatch_raises(self):
        """Mismatched lengths should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            shift_risk([0.5, 0.5], [0.3, 0.3, 0.4])

    def test_empty_allocation_raises(self):
        """Empty allocation should raise ValueError."""
        with pytest.raises(ValueError, match="empty allocation"):
            shift_risk([], [])

    def test_single_asset(self):
        """A single-asset allocation should always return [1.0]."""
        current = [1.0]
        target = [1.0]
        result = shift_risk(current, target, damping=0.5)
        assert abs(result[0] - 1.0) < 1e-9

    def test_output_length_matches_input(self):
        """The output list should have the same length as the inputs."""
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.1, 0.2, 0.3, 0.4]
        result = shift_risk(current, target, damping=0.5)
        assert len(result) == len(current)