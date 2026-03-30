import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.storage_mix import storage_mix
else:
    from programs.storage_mix import storage_mix


class TestNormalization:
    """Tests that verify the output vector is properly normalized to sum to 1."""

    def test_sum_to_one_equal_current_target(self):
        """Output elements should sum to 1 when current equals target."""
        result = storage_mix([0.5, 0.5], [0.5, 0.5], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_sum_to_one_different_current_target(self):
        """Output elements should sum to 1 when current and target differ."""
        result = storage_mix([0.3, 0.7], [0.6, 0.4], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_sum_to_one_three_tiers(self):
        """Output elements should sum to 1 for a three-tier allocation."""
        result = storage_mix([0.2, 0.3, 0.5], [0.4, 0.4, 0.2], damping=0.3)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_sum_to_one_damping_one(self):
        """When damping is 1, output should equal normalized target and sum to 1."""
        result = storage_mix([0.1, 0.9], [0.8, 0.2], damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalized_values_damping_one(self):
        """When damping is 1, output should match the normalized target vector."""
        result = storage_mix([0.1, 0.9], [0.8, 0.2], damping=1.0)
        assert abs(result[0] - 0.8) < 1e-9
        assert abs(result[1] - 0.2) < 1e-9

    def test_normalized_values_with_non_unit_sum_inputs(self):
        """Normalization should produce correct proportions even when inputs don't sum to 1."""
        result = storage_mix([1.0, 1.0], [1.0, 1.0], damping=0.5)
        assert abs(result[0] - 0.5) < 1e-9
        assert abs(result[1] - 0.5) < 1e-9


class TestBasicBehavior:
    """Tests that verify basic behavior that works on both versions."""

    def test_shape_mismatch_raises(self):
        """Mismatched lengths of current and target should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            storage_mix([0.5, 0.5], [0.3, 0.3, 0.4])

    def test_empty_allocation_raises(self):
        """Empty allocation should raise ValueError."""
        with pytest.raises(ValueError, match="empty allocation"):
            storage_mix([], [])

    def test_invalid_damping_raises(self):
        """Damping outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError):
            storage_mix([0.5, 0.5], [0.5, 0.5], damping=1.5)

    def test_output_length_matches_input(self):
        """Output should have the same number of elements as input."""
        result = storage_mix([0.2, 0.3, 0.5], [0.4, 0.4, 0.2], damping=0.3)
        assert len(result) == 3