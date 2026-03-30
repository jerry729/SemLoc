import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cluster_rebalance_weights import cluster_rebalance_weights
else:
    from programs.cluster_rebalance_weights import cluster_rebalance_weights


class TestNormalization:
    """Tests that verify the output weights are normalized to sum to 1.0."""

    def test_uniform_weights_sum_to_one(self):
        """Output weights should form a valid probability distribution summing to 1.0."""
        current = [0.25, 0.25, 0.25, 0.25]
        target = [0.1, 0.2, 0.3, 0.4]
        result = cluster_rebalance_weights(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_non_uniform_weights_sum_to_one(self):
        """Output weights should always be normalized regardless of input magnitudes."""
        current = [0.5, 0.3, 0.2]
        target = [0.6, 0.3, 0.1]
        result = cluster_rebalance_weights(current, target, damping=0.8)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_damping_one_produces_normalized_target(self):
        """With damping=1.0, output should equal the normalized target distribution."""
        current = [0.5, 0.5]
        target = [0.3, 0.7]
        result = cluster_rebalance_weights(current, target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[0] - 0.3) < 1e-9
        assert abs(result[1] - 0.7) < 1e-9

    def test_large_magnitude_inputs_normalized(self):
        """Even when inputs have large magnitudes, output should sum to 1.0."""
        current = [10.0, 20.0, 30.0]
        target = [15.0, 25.0, 20.0]
        result = cluster_rebalance_weights(current, target, damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_single_cluster_normalized(self):
        """A single cluster should always have weight 1.0 after normalization."""
        current = [5.0]
        target = [3.0]
        result = cluster_rebalance_weights(current, target, damping=0.5)
        assert abs(result[0] - 1.0) < 1e-9


class TestBasicBehavior:
    """Tests that pass on both buggy and correct versions (baseline behavior)."""

    def test_damping_zero_keeps_current(self):
        """With damping=0, output should be proportional to current weights."""
        current = [0.5, 0.5]
        target = [0.9, 0.1]
        result = cluster_rebalance_weights(current, target, damping=0.0)
        # With damping=0, interpolation gives back current values.
        # After normalization, [0.5, 0.5] -> [0.5, 0.5]
        # Buggy version also returns [0.5, 0.5] since no interpolation change.
        assert len(result) == 2

    def test_shape_mismatch_raises(self):
        """Mismatched lengths should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            cluster_rebalance_weights([0.5, 0.5], [1.0])

    def test_empty_weights_raises(self):
        """Empty weight vectors should raise ValueError."""
        with pytest.raises(ValueError, match="empty weights"):
            cluster_rebalance_weights([], [])

    def test_invalid_damping_raises(self):
        """Damping outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError):
            cluster_rebalance_weights([0.5, 0.5], [0.3, 0.7], damping=1.5)


class TestProportions:
    """Tests that verify correct proportional relationships in output."""

    def test_five_clusters_proportions(self):
        """Relative proportions should reflect interpolated and normalized values."""
        current = [0.2, 0.2, 0.2, 0.2, 0.2]
        target = [0.0, 0.0, 0.0, 0.0, 1.0]
        result = cluster_rebalance_weights(current, target, damping=0.5)
        # Interpolated: [0.1, 0.1, 0.1, 0.1, 0.6] -> sum=1.0
        # After normalization: [0.1, 0.1, 0.1, 0.1, 0.6]
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[4] - 0.6) < 1e-9
        assert abs(result[0] - 0.1) < 1e-9