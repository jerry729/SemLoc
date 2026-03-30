import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.realign_replica import realign_replica
else:
    from programs.realign_replica import realign_replica


class TestNormalization:
    """Tests that verify the output is normalized (sums to 1.0)."""

    def test_equal_weights_sum_to_one(self):
        """Output allocations should sum to 1.0 for equal current and target weights."""
        result = realign_replica([0.5, 0.5], [0.5, 0.5], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_unequal_weights_sum_to_one(self):
        """Output allocations should sum to 1.0 for unequal distributions."""
        result = realign_replica([0.3, 0.7], [0.6, 0.4], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_three_replicas_sum_to_one(self):
        """Output allocations for three replicas should sum to 1.0."""
        result = realign_replica([0.2, 0.3, 0.5], [0.4, 0.4, 0.2], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9

    def test_damping_one_snaps_to_target_normalized(self):
        """With damping=1.0, output should equal target and sum to 1.0."""
        target = [0.25, 0.25, 0.25, 0.25]
        result = realign_replica([0.1, 0.2, 0.3, 0.4], target, damping=1.0)
        assert abs(sum(result) - 1.0) < 1e-9
        for r, t in zip(result, target):
            assert abs(r - t) < 1e-6

    def test_damping_zero_keeps_current_normalized(self):
        """With damping=0.0, output should reflect current allocations normalized to 1.0."""
        current = [0.5, 0.5]
        result = realign_replica(current, [0.8, 0.2], damping=0.0)
        assert abs(sum(result) - 1.0) < 1e-9


class TestProportions:
    """Tests that verify correct proportional relationships in output."""

    def test_single_replica_normalized(self):
        """A single replica should have allocation of 1.0 after normalization."""
        result = realign_replica([1.0], [1.0], damping=0.5)
        assert abs(result[0] - 1.0) < 1e-9

    def test_proportions_after_blending(self):
        """After blending and normalizing, proportions should reflect the damped mix."""
        current = [0.4, 0.6]
        target = [0.8, 0.2]
        result = realign_replica(current, target, damping=0.5)
        # Blended: [0.4 + 0.4*0.5, 0.6 + (-0.4)*0.5] = [0.6, 0.4]
        # Normalized: [0.6, 0.4]
        assert abs(result[0] - 0.6) < 1e-6
        assert abs(result[1] - 0.4) < 1e-6

    def test_large_current_values_still_normalized(self):
        """Even if current values are large (not summing to 1), output should be normalized."""
        result = realign_replica([5.0, 5.0], [5.0, 5.0], damping=0.5)
        assert abs(sum(result) - 1.0) < 1e-9
        assert abs(result[0] - 0.5) < 1e-6
        assert abs(result[1] - 0.5) < 1e-6


class TestBasicBehavior:
    """Tests that pass on both versions — basic validation and structure."""

    def test_returns_list_of_correct_length(self):
        """Output should be a list with the same number of elements as input."""
        result = realign_replica([0.5, 0.5], [0.5, 0.5], damping=0.5)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_mismatched_lengths_raises(self):
        """Mismatched input lengths should raise ValueError."""
        with pytest.raises(ValueError, match="shape mismatch"):
            realign_replica([0.5], [0.5, 0.5], damping=0.5)

    def test_empty_input_raises(self):
        """Empty inputs should raise ValueError."""
        with pytest.raises(ValueError, match="empty allocation"):
            realign_replica([], [], damping=0.5)

    def test_invalid_damping_raises(self):
        """Damping outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError):
            realign_replica([0.5, 0.5], [0.5, 0.5], damping=1.5)