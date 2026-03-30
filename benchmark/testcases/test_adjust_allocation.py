import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.adjust_allocation import adjust_allocation
else:
    from programs.adjust_allocation import adjust_allocation


def test_shape_mismatch_raises():
    """Current and target vectors must have the same number of assets."""
    with pytest.raises(ValueError, match="shape mismatch"):
        adjust_allocation([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """An empty portfolio is not a valid input."""
    with pytest.raises(ValueError, match="empty allocation"):
        adjust_allocation([], [])


def test_negative_weight_raises():
    """All input weights must be non-negative."""
    with pytest.raises(ValueError):
        adjust_allocation([-0.1, 1.1], [0.5, 0.5])


def test_non_numeric_weight_raises():
    """Weights must be numeric types."""
    with pytest.raises(TypeError):
        adjust_allocation(["a", "b"], [0.5, 0.5])


def test_single_asset_stays_at_one():
    """A single-asset portfolio should always have weight 1.0."""
    result = adjust_allocation([1.0], [1.0])
    assert abs(result[0] - 1.0) < 1e-9


def test_equal_current_and_target_normalised():
    """When current equals target, output weights must sum to 1.0."""
    current = [0.25, 0.25, 0.25, 0.25]
    result = adjust_allocation(current, current)
    assert abs(sum(result) - 1.0) < 1e-9


def test_two_asset_weights_sum_to_one():
    """After rebalancing a two-asset portfolio the weights must sum to 1.0."""
    result = adjust_allocation([0.6, 0.4], [0.5, 0.5])
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_reaches_target():
    """With damping=1.0, the output must equal the normalised target."""
    target = [0.3, 0.3, 0.4]
    result = adjust_allocation([0.5, 0.3, 0.2], target, damping=1.0)
    assert abs(sum(result) - 1.0) < 1e-9
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-9


def test_three_asset_normalisation():
    """Three-asset rebalancing must produce weights that sum to 1.0."""
    result = adjust_allocation([0.5, 0.3, 0.2], [0.1, 0.1, 0.8])
    assert abs(sum(result) - 1.0) < 1e-9


def test_unequal_current_sum_still_normalised():
    """Even if current weights do not sum to 1, output must be normalised."""
    result = adjust_allocation([0.8, 0.8], [0.5, 0.5], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
