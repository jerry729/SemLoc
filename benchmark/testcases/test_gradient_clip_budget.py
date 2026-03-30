import pytest
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.gradient_clip_budget import gradient_clip_budget
else:
    from programs.gradient_clip_budget import gradient_clip_budget


def test_empty_gradient_list():
    """An empty gradient list should return an empty list without error."""
    result = gradient_clip_budget([])
    assert result == []


def test_negative_max_norm_raises():
    """A negative clipping threshold is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        gradient_clip_budget([1.0, 2.0], max_norm=-1.0)


def test_zero_max_norm_raises():
    """A zero clipping threshold is invalid and must raise ValueError."""
    with pytest.raises(ValueError):
        gradient_clip_budget([1.0], max_norm=0.0)


def test_gradients_within_budget_unchanged():
    """Gradients whose norm is within the budget should be returned as-is."""
    grads = [0.1, 0.2, 0.3]
    result = gradient_clip_budget(grads, max_norm=5.0)
    for r, g in zip(result, grads):
        assert abs(r - g) < 1e-9


def test_single_gradient_within_budget():
    """A single scalar gradient within the budget is returned unchanged."""
    result = gradient_clip_budget([0.5], max_norm=1.0)
    assert abs(result[0] - 0.5) < 1e-9


def test_clipped_norm_equals_max_norm():
    """After clipping, the L2 norm of the output should equal max_norm."""
    grads = [3.0, 4.0]
    max_norm = 1.0
    result = gradient_clip_budget(grads, max_norm=max_norm)
    clipped_norm = math.sqrt(sum(r * r for r in result))
    assert abs(clipped_norm - max_norm) < 1e-6


def test_clipped_uniform_gradients_norm():
    """Uniform large gradients should be rescaled so that their L2 norm equals max_norm."""
    grads = [10.0, 10.0, 10.0, 10.0]
    max_norm = 2.0
    result = gradient_clip_budget(grads, max_norm=max_norm)
    clipped_norm = math.sqrt(sum(r * r for r in result))
    assert abs(clipped_norm - max_norm) < 1e-6


def test_direction_preserved_after_clipping():
    """Clipping should preserve the relative direction (ratios) of gradient components."""
    grads = [6.0, 8.0]
    result = gradient_clip_budget(grads, max_norm=1.0)
    ratio_original = grads[0] / grads[1]
    ratio_clipped = result[0] / result[1]
    assert abs(ratio_original - ratio_clipped) < 1e-9


def test_large_gradient_vector_clipped_correctly():
    """A high-dimensional gradient vector exceeding the budget must be clipped to max_norm."""
    grads = [1.0] * 100
    max_norm = 5.0
    result = gradient_clip_budget(grads, max_norm=max_norm)
    clipped_norm = math.sqrt(sum(r * r for r in result))
    assert abs(clipped_norm - max_norm) < 1e-6


def test_scale_factor_precision():
    """The scaling factor should be max_norm / norm, producing exact rescaling."""
    grads = [3.0, 4.0]
    max_norm = 2.5
    original_norm = math.sqrt(sum(g * g for g in grads))
    expected_scale = max_norm / original_norm
    result = gradient_clip_budget(grads, max_norm=max_norm)
    for r, g in zip(result, grads):
        assert abs(r - g * expected_scale) < 1e-6
