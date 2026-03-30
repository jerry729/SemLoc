import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.priority_mix import priority_mix
else:
    from programs.priority_mix import priority_mix


def test_shape_mismatch_raises():
    """Current and target must have the same number of slots."""
    with pytest.raises(ValueError, match="shape mismatch"):
        priority_mix([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation is invalid and must be rejected."""
    with pytest.raises(ValueError, match="empty allocation"):
        priority_mix([], [])


def test_invalid_damping_raises():
    """Damping factor outside the valid range must be rejected."""
    with pytest.raises(ValueError):
        priority_mix([0.5, 0.5], [0.3, 0.7], damping=0.0)


def test_single_slot_returns_one():
    """A single-slot allocation should always normalise to 1.0."""
    result = priority_mix([1.0], [1.0])
    assert len(result) == 1
    assert abs(result[0] - 1.0) < 1e-9


def test_damping_one_snaps_to_target():
    """With damping=1.0 the result should equal the normalised target."""
    target = [0.2, 0.3, 0.5]
    result = priority_mix([0.1, 0.1, 0.8], target, damping=1.0)
    total_target = sum(target)
    for i in range(len(target)):
        assert abs(result[i] - target[i] / total_target) < 1e-9


def test_weights_sum_to_one_uniform():
    """Weights must sum to 1.0 after rebalancing a uniform allocation."""
    result = priority_mix([0.25, 0.25, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_weights_sum_to_one_skewed():
    """Weights must sum to 1.0 even when current allocation is heavily skewed."""
    result = priority_mix([0.9, 0.05, 0.05], [0.33, 0.33, 0.34])
    assert abs(sum(result) - 1.0) < 1e-9


def test_normalised_proportions_two_slots():
    """Resulting weights should reflect the blended proportions after normalisation."""
    current = [0.6, 0.4]
    target = [0.4, 0.6]
    result = priority_mix(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_idempotent_on_equal_distributions():
    """When current equals target the distribution should remain unchanged and normalised."""
    dist = [0.2, 0.3, 0.5]
    result = priority_mix(dist, dist, damping=0.7)
    assert abs(sum(result) - 1.0) < 1e-9
    for i in range(len(dist)):
        assert abs(result[i] - dist[i]) < 1e-9


def test_weights_sum_to_one_large_values():
    """Normalisation must hold even when raw weights are large."""
    current = [10.0, 20.0, 30.0]
    target = [15.0, 25.0, 35.0]
    result = priority_mix(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
