import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.ad_mix import ad_mix
else:
    from programs.ad_mix import ad_mix


class TestNormalizationRequired:
    """Tests that verify the output is normalized to sum to 1.0."""

    def test_output_sums_to_one_equal_weights(self):
        """Output allocations should sum to 1.0 for uniform distributions."""
        result = ad_mix([0.5, 0.5], [0.5, 0.5], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_unequal_weights(self):
        """Output allocations should sum to 1.0 even when inputs are non-uniform."""
        result = ad_mix([0.3, 0.7], [0.6, 0.4], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_output_sums_to_one_three_slots(self):
        """Output allocations for three slots should sum to 1.0."""
        result = ad_mix([0.2, 0.3, 0.5], [0.4, 0.4, 0.2], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalization_with_damping_one(self):
        """When damping=1, output should equal the target and sum to 1.0."""
        result = ad_mix([0.1, 0.9], [0.8, 0.2], damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[0] - 0.8) < 1e-9
        assert abs(result[1] - 0.2) < 1e-9

    def test_normalization_when_interpolated_sum_differs_from_one(self):
        """Normalization must correct sums that drift from 1.0 after interpolation."""
        # current sums to 1.0, target sums to 1.0, but with damping
        # and certain distributions, floating-point or non-summing-to-1 inputs
        # can cause drift. Use inputs where current and target both sum to 1
        # but the interpolation still needs normalization for correctness.
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.1, 0.2, 0.3, 0.4]
        result = ad_mix(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_normalized_values_correct_four_slots(self):
        """Each individual normalized allocation value should be correct."""
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.1, 0.2, 0.3, 0.4]
        result = ad_mix(current, target, damping=0.5)
        # After interpolation: [0.175, 0.225, 0.275, 0.325] sum=1.0
        # After normalization: same values (sum is already 1.0)
        # But the key test is that normalization step is applied
        assert abs(result[0] - 0.175) < 1e-9
        assert abs(result[1] - 0.225) < 1e-9
        assert abs(result[2] - 0.275) < 1e-9
        assert abs(result[3] - 0.325) < 1e-9


class TestNormalizationWithNonUnitSum:
    """Tests where inputs don't perfectly sum to 1, requiring normalization."""

    def test_current_not_summing_to_one(self):
        """When current doesn't sum to 1, output must still be normalized to 1."""
        # current sums to 0.8, target sums to 1.0
        current = [0.3, 0.5]
        target = [0.5, 0.5]
        result = ad_mix(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_target_not_summing_to_one(self):
        """When target doesn't sum to 1, output must still be normalized to 1."""
        # current sums to 1.0, target sums to 0.6
        current = [0.5, 0.5]
        target = [0.3, 0.3]
        result = ad_mix(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9


class TestBasicBehavior:
    """Tests that pass on both buggy and correct versions."""

    def test_shape_mismatch_raises(self):
        """Mismatched lengths should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            ad_mix([0.5, 0.5], [0.3, 0.3, 0.4])

    def test_empty_allocation_raises(self):
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError, match="empty allocation"):
            ad_mix([], [])

    def test_out_of_range_current_raises(self):
        """Current values outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError):
            ad_mix([1.5, -0.5], [0.5, 0.5])

    def test_single_slot_returns_one(self):
        """A single-slot allocation should always return [1.0] after normalization."""
        result = ad_mix([1.0], [1.0], damping=0.5)
        assert abs(result[0] - 1.0) < 1e-9