import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.adjust_portfolio import adjust_portfolio
else:
    from programs.adjust_portfolio import adjust_portfolio


class TestNormalization:
    """Tests that verify the output weights are normalized to sum to 1.0."""

    def test_equal_weights_sum_to_one(self):
        """Output weights for a simple two-asset portfolio should sum to 1.0."""
        result = adjust_portfolio([0.5, 0.5], [0.5, 0.5])
        assert abs(sum(result) - 1.0) < 1e-9

    def test_unequal_current_target_sum_to_one(self):
        """Output weights should sum to 1.0 when current and target differ."""
        result = adjust_portfolio([0.3, 0.7], [0.6, 0.4], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_three_asset_normalization(self):
        """A three-asset portfolio result should be normalized to sum to 1.0."""
        result = adjust_portfolio([0.2, 0.3, 0.5], [0.4, 0.4, 0.2], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_damping_one_snaps_to_target_normalized(self):
        """With damping=1.0, result should equal target and sum to 1.0."""
        target = [0.25, 0.25, 0.25, 0.25]
        result = adjust_portfolio([0.1, 0.2, 0.3, 0.4], target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9
        for r, t in zip(result, target):
            assert abs(r - t) < 1e-9

    def test_individual_weights_are_normalized(self):
        """Each individual weight should reflect normalization, not raw blending."""
        result = adjust_portfolio([0.6, 0.4], [0.8, 0.2], damping=0.5)
        # Raw blend: [0.7, 0.3], sum=1.0, normalized: [0.7, 0.3]
        # This case happens to sum to 1.0 already, so let's check values
        assert abs(result[0] - 0.7) < 1e-9
        assert abs(result[1] - 0.3) < 1e-9
        assert abs(sum(result) - 1.0) < 1e-9


class TestNormalizationWithSkewedInputs:
    """Tests where raw blending would NOT sum to 1.0 without normalization."""

    def test_current_not_summing_to_one_gets_normalized(self):
        """When current weights don't sum to 1.0, output should still be normalized."""
        # current sums to 0.8, target sums to 1.0, damping=0.5
        # raw blend: [0.1+0.15, 0.3+0.05, 0.4-0.1] = [0.25, 0.35, 0.3] sum=0.9
        # normalized: [0.25/0.9, 0.35/0.9, 0.3/0.9]
        result = adjust_portfolio([0.1, 0.3, 0.4], [0.4, 0.4, 0.2], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_damping_zero_preserves_current_normalized(self):
        """With damping=0.0, result should be the current weights, normalized."""
        current = [0.2, 0.3, 0.5]
        result = adjust_portfolio(current, [0.5, 0.3, 0.2], damping=0.0)
        assert abs(sum(result) - 1.0) < 1e-9
        # Current already sums to 1.0, so values should match
        for r, c in zip(result, current):
            assert abs(r - c) < 1e-9

    def test_small_damping_sum_to_one(self):
        """With small damping, output should still sum to 1.0."""
        result = adjust_portfolio([0.1, 0.9], [0.9, 0.1], damping=0.1)
        assert abs(sum(result) - 1.0) < 1e-9


class TestBasicBehavior:
    """Tests for basic functionality that should pass on both versions."""

    def test_shape_mismatch_raises(self):
        """Mismatched lengths should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            adjust_portfolio([0.5, 0.5], [1.0])

    def test_empty_raises(self):
        """Empty inputs should raise ValueError."""
        with pytest.raises(ValueError, match="empty allocation"):
            adjust_portfolio([], [])

    def test_negative_weight_raises(self):
        """Negative weights should raise ValueError."""
        with pytest.raises(ValueError):
            adjust_portfolio([-0.1, 1.1], [0.5, 0.5])

    def test_returns_list(self):
        """Result should be a list."""
        result = adjust_portfolio([0.5, 0.5], [0.5, 0.5])
        assert isinstance(result, list)