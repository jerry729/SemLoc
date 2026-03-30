import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_weight import shift_weight
else:
    from programs.shift_weight import shift_weight


def test_shape_mismatch_raises():
    """Vectors of different lengths must be rejected."""
    with pytest.raises(ValueError, match="shape mismatch"):
        shift_weight([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """An empty allocation vector is not a valid portfolio."""
    with pytest.raises(ValueError, match="empty allocation"):
        shift_weight([], [])


def test_damping_out_of_range_raises():
    """Damping outside (0, 1] must be rejected."""
    with pytest.raises(ValueError):
        shift_weight([0.5, 0.5], [0.3, 0.7], damping=0.0)


def test_identical_current_and_target():
    """When current equals target, weights should remain unchanged after normalization."""
    result = shift_weight([0.5, 0.5], [0.5, 0.5])
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_full_damping_reaches_target():
    """With damping=1.0, the result must equal the target distribution."""
    result = shift_weight([0.2, 0.8], [0.6, 0.4], damping=1.0)
    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.4) < 1e-9


def test_output_sums_to_one_equal_weights():
    """Rebalanced portfolio weights must always sum to 1.0."""
    result = shift_weight([0.25, 0.25, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_asymmetric():
    """Weights must sum to unity even for heavily skewed distributions."""
    result = shift_weight([0.9, 0.05, 0.05], [0.1, 0.45, 0.45])
    assert abs(sum(result) - 1.0) < 1e-9


def test_partial_shift_proportions():
    """A partial shift should produce normalized weights between current and target."""
    current = [0.3, 0.7]
    target = [0.7, 0.3]
    result = shift_weight(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_three_asset_normalization():
    """A three-asset portfolio must be properly normalized after shifting."""
    result = shift_weight([0.5, 0.3, 0.2], [0.2, 0.3, 0.5], damping=0.7)
    assert abs(sum(result) - 1.0) < 1e-9


def test_unequal_sums_still_normalized():
    """Even if current weights don't sum to 1, the output must be normalized."""
    result = shift_weight([0.4, 0.4, 0.4], [0.1, 0.1, 0.1], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
