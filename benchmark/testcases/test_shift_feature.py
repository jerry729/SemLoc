import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_feature import shift_feature
else:
    from programs.shift_feature import shift_feature


def test_mismatched_lengths_raises():
    """Vectors of different lengths must be rejected."""
    with pytest.raises(ValueError, match="shape mismatch"):
        shift_feature([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation vector is not a valid input."""
    with pytest.raises(ValueError):
        shift_feature([], [])


def test_identity_shift_when_current_equals_target():
    """When current already equals target, the result should still be normalized."""
    result = shift_feature([0.5, 0.5], [0.5, 0.5])
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_snaps_to_target():
    """With damping=1.0 the output distribution should match the target distribution."""
    target = [0.2, 0.3, 0.5]
    result = shift_feature([0.1, 0.1, 0.8], target, damping=1.0)
    assert abs(sum(result) - 1.0) < 1e-9
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-9


def test_output_sums_to_one_uniform():
    """A uniform allocation shifted toward a skewed target must still sum to 1."""
    result = shift_feature([0.25, 0.25, 0.25, 0.25], [1.0, 0.0, 0.0, 0.0])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_varied_damping():
    """The result is a valid probability distribution regardless of damping."""
    result = shift_feature([0.6, 0.4], [0.3, 0.7], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_proportions_shift_toward_target():
    """Each component should move in the direction of its target."""
    current = [0.1, 0.9]
    target = [0.9, 0.1]
    result = shift_feature(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert result[0] > 0.1
    assert result[1] < 0.9


def test_three_component_normalization():
    """A three-component shift must produce a normalized distribution."""
    result = shift_feature([0.1, 0.2, 0.7], [0.4, 0.4, 0.2], damping=0.3)
    assert abs(sum(result) - 1.0) < 1e-9


def test_single_element_stays_at_one():
    """A single-element allocation is trivially normalized to 1.0."""
    result = shift_feature([1.0], [1.0], damping=0.5)
    assert len(result) == 1
    assert abs(result[0] - 1.0) < 1e-9


def test_large_values_still_normalized():
    """Even when raw weights are large, the output must be a valid distribution."""
    result = shift_feature([10.0, 20.0], [30.0, 40.0], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
