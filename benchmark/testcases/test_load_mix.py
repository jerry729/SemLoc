import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.load_mix import load_mix
else:
    from programs.load_mix import load_mix


def test_shape_mismatch_raises():
    """Allocations of different lengths must be rejected."""
    with pytest.raises(ValueError, match="shape mismatch"):
        load_mix([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """An empty current allocation vector is not meaningful."""
    with pytest.raises(ValueError, match="empty allocation"):
        load_mix([], [])


def test_damping_out_of_range_raises():
    """Damping factors outside [0, 1] must be rejected."""
    with pytest.raises(ValueError):
        load_mix([0.5, 0.5], [0.3, 0.7], damping=1.5)


def test_damping_zero_keeps_current_proportions():
    """With damping=0 the output proportions must equal the normalised current."""
    result = load_mix([0.6, 0.4], [0.2, 0.8], damping=0.0)
    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.4) < 1e-9


def test_damping_one_reaches_target():
    """With damping=1 the output must equal the normalised target."""
    result = load_mix([0.6, 0.4], [0.2, 0.8], damping=1.0)
    assert abs(result[0] - 0.2) < 1e-9
    assert abs(result[1] - 0.8) < 1e-9


def test_result_sums_to_one_uniform():
    """Rebalanced allocations must always sum to 1.0."""
    result = load_mix([0.25, 0.25, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4])
    assert abs(sum(result) - 1.0) < 1e-9


def test_result_sums_to_one_skewed():
    """Even with highly skewed inputs, the output must be a proper distribution."""
    result = load_mix([0.9, 0.05, 0.05], [0.1, 0.1, 0.8])
    assert abs(sum(result) - 1.0) < 1e-9


def test_normalised_values_three_servers():
    """For three servers with default damping, each normalised weight should match expected."""
    current = [0.5, 0.3, 0.2]
    target = [0.3, 0.4, 0.3]
    result = load_mix(current, target)
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.4) < 1e-9
    assert abs(result[1] - 0.35) < 1e-9
    assert abs(result[2] - 0.25) < 1e-9


def test_single_element_normalisation():
    """A single-element allocation must normalise to exactly 1.0."""
    result = load_mix([3.0], [7.0])
    assert abs(result[0] - 1.0) < 1e-9


def test_equal_current_and_target():
    """When current equals target the output must still be normalised."""
    result = load_mix([0.4, 0.6], [0.4, 0.6])
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.4) < 1e-9
    assert abs(result[1] - 0.6) < 1e-9
