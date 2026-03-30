import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bandwidth_rebalance import bandwidth_rebalance
else:
    from programs.bandwidth_rebalance import bandwidth_rebalance


def test_shape_mismatch_raises():
    """Inputs of different lengths must be rejected immediately."""
    with pytest.raises(ValueError, match="shape mismatch"):
        bandwidth_rebalance([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation is not meaningful and must be rejected."""
    with pytest.raises(ValueError, match="empty allocation"):
        bandwidth_rebalance([], [])


def test_single_channel_stays_at_one():
    """A single-channel allocation must always return weight 1.0."""
    result = bandwidth_rebalance([1.0], [1.0])
    assert len(result) == 1
    assert abs(result[0] - 1.0) < 1e-9


def test_already_on_target_remains_stable():
    """When current equals target, weights must not drift."""
    current = [0.25, 0.25, 0.25, 0.25]
    target = [0.25, 0.25, 0.25, 0.25]
    result = bandwidth_rebalance(current, target)
    for w in result:
        assert abs(w - 0.25) < 1e-9


def test_weights_sum_to_one_uniform():
    """After rebalancing, weights must sum to 1.0 for a uniform target."""
    current = [0.5, 0.3, 0.2]
    target = [0.33, 0.34, 0.33]
    result = bandwidth_rebalance(current, target)
    assert abs(sum(result) - 1.0) < 1e-9


def test_weights_sum_to_one_skewed():
    """Rebalanced weights must sum to 1.0 even with a skewed target."""
    current = [0.1, 0.9]
    target = [0.8, 0.2]
    result = bandwidth_rebalance(current, target)
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_reaches_target():
    """With damping=1.0, the output must equal the target distribution (normalised)."""
    current = [0.6, 0.4]
    target = [0.3, 0.7]
    result = bandwidth_rebalance(current, target, damping=1.0)
    assert abs(result[0] - 0.3) < 1e-9
    assert abs(result[1] - 0.7) < 1e-9


def test_zero_damping_preserves_current():
    """With damping=0.0, the output must remain the current distribution (normalised)."""
    current = [0.6, 0.4]
    target = [0.3, 0.7]
    result = bandwidth_rebalance(current, target, damping=0.0)
    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.4) < 1e-9


def test_three_channels_normalized():
    """A three-channel rebalance must produce normalised weights."""
    current = [0.5, 0.3, 0.2]
    target = [0.1, 0.1, 0.8]
    result = bandwidth_rebalance(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_large_allocation_normalized():
    """Even with many channels, output weights must be a valid probability distribution."""
    n = 100
    current = [1.0 / n] * n
    target = [float(i) for i in range(n)]
    result = bandwidth_rebalance(current, target, damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert all(w >= 0.0 for w in result)
