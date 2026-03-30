import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_traffic import shift_traffic
else:
    from programs.shift_traffic import shift_traffic


def test_shape_mismatch_raises():
    """Current and target vectors must have identical length."""
    with pytest.raises(ValueError, match="shape mismatch"):
        shift_traffic([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation vector is invalid for traffic shifting."""
    with pytest.raises(ValueError, match="empty allocation"):
        shift_traffic([], [])


def test_negative_weight_raises():
    """Negative weights are not valid traffic allocations."""
    with pytest.raises(ValueError):
        shift_traffic([-0.1, 1.1], [0.5, 0.5])


def test_single_service_stays_at_one():
    """A single-service deployment should always keep weight 1.0."""
    result = shift_traffic([1.0], [1.0])
    assert len(result) == 1
    assert abs(result[0] - 1.0) < 1e-9


def test_identical_current_and_target():
    """When current equals target the result should remain normalised to 1."""
    result = shift_traffic([0.5, 0.5], [0.5, 0.5])
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.5) < 1e-9


def test_output_sums_to_one_uniform():
    """Updated weights must always form a valid probability distribution."""
    result = shift_traffic([0.25, 0.25, 0.25, 0.25], [0.4, 0.3, 0.2, 0.1])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_skewed():
    """Even with highly skewed targets, the output must sum to 1."""
    result = shift_traffic([0.1, 0.9], [0.9, 0.1], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_damping_one_snaps_to_target():
    """With damping=1.0 the allocation should match the target exactly."""
    target = [0.6, 0.3, 0.1]
    result = shift_traffic([0.2, 0.3, 0.5], target, damping=1.0)
    assert abs(sum(result) - 1.0) < 1e-9
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-9


def test_proportional_shift_two_services():
    """Weights should move proportionally toward the target allocation."""
    current = [0.8, 0.2]
    target = [0.2, 0.8]
    result = shift_traffic(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert result[0] < current[0]
    assert result[1] > current[1]


def test_non_unit_current_normalised_output():
    """If current weights don't sum to 1 the output should still be normalised."""
    result = shift_traffic([2.0, 3.0], [0.5, 0.5], damping=0.7)
    assert abs(sum(result) - 1.0) < 1e-9
