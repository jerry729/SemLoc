import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.budget_mix import budget_mix
else:
    from programs.budget_mix import budget_mix


# Tests that PASS on both versions (baseline behavior)

def test_shape_mismatch_raises():
    """Vectors of different lengths should raise ValueError."""
    with pytest.raises(ValueError, match="shape mismatch"):
        budget_mix([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """Empty allocation vectors should raise ValueError."""
    with pytest.raises(ValueError, match="empty allocation"):
        budget_mix([], [])


def test_identical_current_and_target():
    """When current equals target and both sum to 1, output should equal input."""
    result = budget_mix([0.5, 0.5], [0.5, 0.5], damping=0.3)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_damping_one_snaps_to_target():
    """With damping=1.0, output should match the target (after normalization)."""
    result = budget_mix([0.3, 0.7], [0.6, 0.4], damping=1.0)
    assert abs(result[0] - 0.6) < 1e-9
    assert abs(result[1] - 0.4) < 1e-9


# Tests that FAIL on buggy, PASS on correct (normalization tests)

def test_output_sums_to_one_unequal_weights():
    """Output allocation should always sum to 1.0 after normalization."""
    current = [0.2, 0.2, 0.2]
    target = [0.4, 0.4, 0.4]
    result = budget_mix(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_output_sums_to_one_two_elements():
    """A two-element allocation that doesn't naturally sum to 1 must be normalized."""
    current = [0.1, 0.1]
    target = [0.3, 0.3]
    result = budget_mix(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_normalization_with_asymmetric_inputs():
    """Asymmetric current and target that don't sum to 1 should produce normalized output."""
    current = [0.1, 0.2, 0.3]
    target = [0.5, 0.3, 0.1]
    result = budget_mix(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_normalization_preserves_proportions():
    """Normalized output should have correct relative proportions."""
    current = [0.2, 0.2, 0.2]
    target = [0.4, 0.4, 0.4]
    result = budget_mix(current, target, damping=0.5)
    # All three values should be equal since current and target are uniform
    assert abs(result[0] - result[1]) < 1e-9
    assert abs(result[1] - result[2]) < 1e-9
    # Each should be 1/3
    assert abs(result[0] - 1.0/3.0) < 1e-9


def test_output_sums_to_one_with_default_damping():
    """With default damping and non-unit-sum inputs, output must still sum to 1."""
    current = [0.0, 0.0, 0.5]
    target = [0.5, 0.5, 0.0]
    result = budget_mix(current, target)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_normalization_four_elements():
    """Four-element allocation with low weights should be normalized to sum to 1."""
    current = [0.1, 0.1, 0.1, 0.1]
    target = [0.2, 0.2, 0.2, 0.2]
    result = budget_mix(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9
    # All should be equal: 0.25 each
    for v in result:
        assert abs(v - 0.25) < 1e-9