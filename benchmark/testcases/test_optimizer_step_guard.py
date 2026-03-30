import pytest
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.optimizer_step_guard import optimizer_step_guard
else:
    from programs.optimizer_step_guard import optimizer_step_guard


def test_normal_loss_allows_step():
    """A typical finite loss well below the threshold should allow the step."""
    assert optimizer_step_guard(0.5) is True


def test_zero_loss_allows_step():
    """A zero loss is valid and the optimizer step should proceed."""
    assert optimizer_step_guard(0.0) is True


def test_loss_exceeding_max_skips_step():
    """Loss above the configurable max_loss must cause the step to be skipped."""
    assert optimizer_step_guard(2e6) is False


def test_loss_exactly_at_max_allows_step():
    """Loss exactly equal to max_loss is still within bounds."""
    assert optimizer_step_guard(1e6, max_loss=1e6) is True


def test_negative_loss_raises_value_error():
    """Negative losses are physically meaningless and must raise ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        optimizer_step_guard(-1.0)


def test_non_numeric_raises_type_error():
    """String values must be rejected with a TypeError."""
    with pytest.raises(TypeError):
        optimizer_step_guard("hello")


def test_nan_loss_skips_step():
    """NaN loss indicates a numerical failure; the optimizer step must be skipped."""
    assert optimizer_step_guard(float("nan")) is False


def test_nan_with_custom_max_loss_skips_step():
    """NaN losses must be rejected regardless of the max_loss setting."""
    assert optimizer_step_guard(float("nan"), max_loss=1e30) is False


def test_custom_max_loss_boundary():
    """A custom max_loss should correctly gate loss values near the boundary."""
    assert optimizer_step_guard(99.0, max_loss=100.0) is True
    assert optimizer_step_guard(101.0, max_loss=100.0) is False


def test_very_small_positive_loss_allows_step():
    """Extremely small but positive losses should still permit the step."""
    assert optimizer_step_guard(1e-30) is True
