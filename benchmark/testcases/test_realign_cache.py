import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, 'inst', None):
    from instrumented.realign_cache import realign_cache
else:
    from programs.realign_cache import realign_cache


def test_shape_mismatch_raises():
    """Vectors of different lengths must be rejected immediately."""
    with pytest.raises(ValueError, match="shape mismatch"):
        realign_cache([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """An empty allocation vector is not a valid cache configuration."""
    with pytest.raises(ValueError, match="empty allocation"):
        realign_cache([], [])


def test_damping_out_of_range_raises():
    """Damping factors outside [0, 1] are invalid."""
    with pytest.raises(ValueError):
        realign_cache([0.5, 0.5], [0.3, 0.7], damping=1.5)


def test_zero_damping_preserves_proportions():
    """With zero damping the allocation should remain at its original proportions, normalized."""
    result = realign_cache([0.6, 0.4], [0.0, 1.0], damping=0.0)
    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.4) < 1e-9


def test_output_sums_to_one_uniform():
    """The returned distribution must sum to 1.0 for a uniform target."""
    result = realign_cache([0.25, 0.25, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_skewed():
    """The returned distribution must sum to 1.0 even for highly skewed inputs."""
    result = realign_cache([0.9, 0.05, 0.05], [0.1, 0.8, 0.1])
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_reaches_target_proportions():
    """With damping=1.0 the output distribution should match target proportions exactly."""
    target = [0.2, 0.3, 0.5]
    result = realign_cache([0.5, 0.3, 0.2], target, damping=1.0)
    assert abs(sum(result) - 1.0) < 1e-9
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-6


def test_single_tier_returns_unit():
    """A single-tier cache must always return [1.0]."""
    result = realign_cache([1.0], [1.0], damping=0.5)
    assert abs(result[0] - 1.0) < 1e-9


def test_normalization_with_large_weights():
    """Large absolute weights must be normalized so the output sums to 1.0."""
    result = realign_cache([100.0, 200.0], [300.0, 400.0], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9


def test_partial_damping_intermediate_values():
    """At damping=0.5 each weight should be the midpoint, then renormalized to sum to 1."""
    result = realign_cache([0.0, 1.0], [1.0, 0.0], damping=0.5)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9
    assert abs(sum(result) - 1.0) < 1e-9
