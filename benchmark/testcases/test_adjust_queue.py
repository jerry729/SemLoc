import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.adjust_queue import adjust_queue
else:
    from programs.adjust_queue import adjust_queue


# --- Tests that PASS on both versions (baseline behavior) ---

def test_identity_when_current_equals_target():
    """When current equals target, output should equal input (already normalized)."""
    current = [0.5, 0.5]
    target = [0.5, 0.5]
    result = adjust_queue(current, target)
    assert len(result) == 2
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_damping_one_snaps_to_target_normalized():
    """With damping=1, output should snap to target; if target sums to 1, result matches."""
    current = [0.5, 0.5]
    target = [0.7, 0.3]
    result = adjust_queue(current, target, damping=1.0)
    assert len(result) == 2
    assert abs(result[0] - 0.7) < 1e-9
    assert abs(result[1] - 0.3) < 1e-9


def test_shape_mismatch_raises():
    """Mismatched input lengths should raise ValueError."""
    with pytest.raises(ValueError, match="shape mismatch"):
        adjust_queue([0.5, 0.5], [1.0])


def test_empty_allocation_raises():
    """Empty inputs should raise ValueError."""
    with pytest.raises(ValueError, match="empty allocation"):
        adjust_queue([], [])


# --- Tests that PASS on correct version, FAIL on buggy version ---

def test_output_sums_to_one_unequal_weights():
    """The returned allocation weights must always sum to 1.0."""
    current = [0.3, 0.3, 0.3]
    target = [0.4, 0.4, 0.4]
    result = adjust_queue(current, target)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_output_sums_to_one_asymmetric():
    """Normalized output must sum to 1.0 even with asymmetric current and target."""
    current = [0.2, 0.3, 0.4]
    target = [0.5, 0.3, 0.1]
    result = adjust_queue(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_output_sums_to_one_two_queues():
    """Output normalization should ensure sum is 1.0 for two-queue case."""
    current = [0.3, 0.3]
    target = [0.4, 0.4]
    result = adjust_queue(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_output_sums_to_one_small_damping():
    """Even with small damping, the output must be normalized to sum to 1.0."""
    current = [0.1, 0.1, 0.1]
    target = [0.5, 0.3, 0.2]
    result = adjust_queue(current, target, damping=0.1)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9


def test_normalized_proportions_four_queues():
    """Four queues with non-unit-sum inputs should produce normalized output summing to 1."""
    current = [0.2, 0.2, 0.2, 0.2]
    target = [0.3, 0.3, 0.3, 0.3]
    result = adjust_queue(current, target, damping=0.5)
    total = sum(result)
    assert abs(total - 1.0) < 1e-9
    # All should be equal due to symmetry
    for v in result:
        assert abs(v - 0.25) < 1e-9


def test_normalization_preserves_relative_order():
    """After normalization, relative ordering of weights should reflect interpolation."""
    current = [0.2, 0.8]
    target = [0.6, 0.4]
    result = adjust_queue(current, target, damping=0.5)
    # Sum must be 1.0
    assert abs(sum(result) - 1.0) < 1e-9
    # After interpolation: raw = [0.4, 0.6], normalized = [0.4, 0.6]
    assert abs(result[0] - 0.4) < 1e-9
    assert abs(result[1] - 0.6) < 1e-9