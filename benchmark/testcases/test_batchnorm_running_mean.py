import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.batchnorm_running_mean import batchnorm_running_mean
else:
    from programs.batchnorm_running_mean import batchnorm_running_mean


def test_identical_means_unchanged():
    """When the running mean and batch mean are equal, the result should remain the same value."""
    result = batchnorm_running_mean(5.0, 5.0, momentum=0.9)
    assert abs(result - 5.0) < 1e-9


def test_momentum_zero_snaps_to_batch():
    """With momentum=0 the running mean should fully adopt the batch mean."""
    result = batchnorm_running_mean(10.0, 3.0, momentum=0.0)
    assert abs(result - 3.0) < 1e-9


def test_momentum_one_keeps_current():
    """With momentum=1 the running mean should remain at the current value."""
    result = batchnorm_running_mean(10.0, 3.0, momentum=1.0)
    assert abs(result - 10.0) < 1e-9


def test_invalid_momentum_raises():
    """Momentum outside [0, 1] must raise a ValueError."""
    with pytest.raises(ValueError):
        batchnorm_running_mean(1.0, 2.0, momentum=1.5)
    with pytest.raises(ValueError):
        batchnorm_running_mean(1.0, 2.0, momentum=-0.1)


def test_default_momentum_slow_update():
    """With the default momentum of 0.9 the running mean should stay close to the current mean."""
    result = batchnorm_running_mean(100.0, 0.0)
    assert abs(result - 90.0) < 1e-9


def test_half_momentum_averages():
    """Momentum=0.5 should produce the arithmetic mean of the two inputs."""
    result = batchnorm_running_mean(4.0, 8.0, momentum=0.5)
    assert abs(result - 6.0) < 1e-9


def test_high_momentum_preserves_history():
    """A high momentum (0.9) should weight the historical running mean heavily."""
    result = batchnorm_running_mean(10.0, 20.0, momentum=0.9)
    expected = 0.9 * 10.0 + 0.1 * 20.0  # 11.0
    assert abs(result - expected) < 1e-9


def test_low_momentum_follows_batch():
    """A low momentum (0.1) should closely follow the batch mean."""
    result = batchnorm_running_mean(10.0, 20.0, momentum=0.1)
    expected = 0.1 * 10.0 + 0.9 * 20.0  # 19.0
    assert abs(result - expected) < 1e-9


def test_negative_values_correct_ema():
    """Running mean should handle negative values and still obey the EMA formula."""
    result = batchnorm_running_mean(-5.0, 15.0, momentum=0.8)
    expected = 0.8 * (-5.0) + 0.2 * 15.0  # -1.0
    assert abs(result - expected) < 1e-9


def test_near_zero_clamping():
    """Extremely small results should be clamped to zero for numerical stability."""
    result = batchnorm_running_mean(1e-15, 0.0, momentum=0.5)
    assert result == 0.0
