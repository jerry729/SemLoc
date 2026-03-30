import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.realign_power import realign_power
else:
    from programs.realign_power import realign_power


def test_shape_mismatch_raises():
    """Allocations of different lengths must be rejected."""
    with pytest.raises(ValueError, match="shape mismatch"):
        realign_power([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation vector is not a valid input."""
    with pytest.raises(ValueError, match="empty allocation"):
        realign_power([], [])


def test_invalid_damping_raises():
    """Damping values outside [0, 1] must be rejected."""
    with pytest.raises(ValueError):
        realign_power([0.5, 0.5], [0.6, 0.4], damping=1.5)


def test_damping_zero_preserves_current():
    """With zero damping the allocation must stay at the current values, normalised."""
    result = realign_power([0.3, 0.7], [0.5, 0.5], damping=0.0)
    assert abs(result[0] - 0.3) < 1e-9
    assert abs(result[1] - 0.7) < 1e-9


def test_uniform_target_yields_uniform_output():
    """When current equals target, the output distribution should match exactly."""
    result = realign_power([0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25])
    for v in result:
        assert abs(v - 0.25) < 1e-9


def test_output_sums_to_one_basic():
    """The returned allocation must form a valid distribution that sums to 1."""
    result = realign_power([0.2, 0.8], [0.6, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_three_elements():
    """A three-element allocation must be normalised to unit sum after realignment."""
    result = realign_power([0.1, 0.3, 0.6], [0.4, 0.4, 0.2])
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_snaps_to_target():
    """With damping=1.0 the allocation must equal the target distribution."""
    target = [0.1, 0.2, 0.3, 0.4]
    result = realign_power([0.25, 0.25, 0.25, 0.25], target, damping=1.0)
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-9


def test_normalisation_with_large_weights():
    """Large absolute weights should still produce a unit-sum distribution."""
    result = realign_power([10.0, 20.0, 30.0], [15.0, 25.0, 35.0], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_partial_damping_proportions():
    """Partial damping should produce weights strictly between current and target, normalised."""
    current = [0.0, 1.0]
    target = [1.0, 0.0]
    result = realign_power(current, target, damping=0.5)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9
    assert abs(sum(result) - 1.0) < 1e-9
