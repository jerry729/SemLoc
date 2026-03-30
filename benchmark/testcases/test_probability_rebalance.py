import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.probability_rebalance import probability_rebalance
else:
    from programs.probability_rebalance import probability_rebalance


def test_shape_mismatch_raises():
    """Vectors of different lengths must be rejected immediately."""
    with pytest.raises(ValueError, match="shape mismatch"):
        probability_rebalance([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """An empty probability vector is not a valid allocation."""
    with pytest.raises(ValueError, match="empty allocation"):
        probability_rebalance([], [])


def test_invalid_damping_raises():
    """Damping outside [0, 1] is not physically meaningful."""
    with pytest.raises(ValueError):
        probability_rebalance([0.5, 0.5], [0.3, 0.7], damping=1.5)


def test_damping_one_returns_target():
    """With full damping the output must equal the target distribution."""
    result = probability_rebalance([0.5, 0.5], [0.8, 0.2], damping=1.0)
    assert abs(result[0] - 0.8) < 1e-9
    assert abs(result[1] - 0.2) < 1e-9


def test_result_sums_to_one_uniform():
    """The rebalanced distribution must always sum to 1.0."""
    result = probability_rebalance([0.25, 0.25, 0.25, 0.25],
                                   [0.1, 0.2, 0.3, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_result_sums_to_one_skewed():
    """Even with a highly skewed target, the output must be a valid distribution."""
    result = probability_rebalance([0.5, 0.3, 0.2],
                                   [0.9, 0.05, 0.05], damping=0.7)
    assert abs(sum(result) - 1.0) < 1e-9


def test_result_sums_to_one_damping_zero():
    """With zero damping the output equals the current vector, still summing to 1."""
    current = [0.4, 0.35, 0.25]
    result = probability_rebalance(current, [0.1, 0.1, 0.8], damping=0.0)
    assert abs(sum(result) - 1.0) < 1e-9


def test_two_asset_partial_rebalance():
    """Partial rebalance of a two-asset portfolio must produce valid probabilities."""
    result = probability_rebalance([0.6, 0.4], [0.4, 0.6], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_non_normalized_current_gets_normalized():
    """If the raw blended weights don't sum to 1 the function must renormalize."""
    result = probability_rebalance([0.3, 0.3, 0.3],
                                   [0.5, 0.3, 0.2], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_single_asset_always_one():
    """A single-asset allocation must always remain 1.0."""
    result = probability_rebalance([1.0], [1.0], damping=0.5)
    assert abs(result[0] - 1.0) < 1e-9
