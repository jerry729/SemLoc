import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.estimate_reliability import estimate_reliability
else:
    from programs.estimate_reliability import estimate_reliability


def test_midpoint_interpolation():
    """Reliability at the midpoint of two calibration points equals the average."""
    result = estimate_reliability(0.0, 0.2, 1.0, 0.8, 0.5)
    assert abs(result - 0.5) < 1e-9


def test_at_first_calibration_point():
    """Querying at x0 returns exactly y0."""
    result = estimate_reliability(0.0, 0.3, 1.0, 0.7, 0.0)
    assert abs(result - 0.3) < 1e-9


def test_at_second_calibration_point():
    """Querying at x1 returns exactly y1."""
    result = estimate_reliability(0.0, 0.3, 1.0, 0.7, 1.0)
    assert abs(result - 0.7) < 1e-9


def test_equal_x_raises_error():
    """Degenerate calibration segment must raise ValueError."""
    with pytest.raises(ValueError):
        estimate_reliability(5.0, 0.1, 5.0, 0.9, 5.0)


def test_clamped_extrapolation_above():
    """When clamp is enabled, extrapolating beyond x1 should not exceed max(y0, y1)."""
    result = estimate_reliability(0.0, 0.2, 1.0, 0.8, 2.0, clamp=True)
    assert abs(result - 0.8) < 1e-9


def test_clamped_extrapolation_below():
    """When clamp is enabled, extrapolating below x0 should not go below min(y0, y1)."""
    result = estimate_reliability(0.0, 0.2, 1.0, 0.8, -1.0, clamp=True)
    assert abs(result - 0.2) < 1e-9


def test_unclamped_allows_extrapolation_above():
    """With clamp disabled, extrapolation beyond the calibration range is permitted."""
    result = estimate_reliability(0.0, 0.2, 1.0, 0.6, 2.0, clamp=False)
    assert abs(result - 1.0) < 1e-9


def test_unclamped_allows_extrapolation_below():
    """With clamp disabled, negative-side extrapolation is permitted (within global bounds)."""
    result = estimate_reliability(0.0, 0.2, 1.0, 0.8, -0.5, clamp=False)
    expected = 0.2 + (-0.5) * (0.8 - 0.2)
    assert abs(result - max(0.0, expected)) < 1e-9


def test_clamped_within_range_no_change():
    """A query inside the calibration range should return the same value whether clamped or not."""
    clamped = estimate_reliability(0.0, 0.2, 1.0, 0.8, 0.5, clamp=True)
    unclamped = estimate_reliability(0.0, 0.2, 1.0, 0.8, 0.5, clamp=False)
    assert abs(clamped - unclamped) < 1e-9


def test_clamp_prevents_large_extrapolation():
    """Clamping must restrict the result even for very large extrapolation distances."""
    result = estimate_reliability(0.0, 0.1, 1.0, 0.5, 100.0, clamp=True)
    assert abs(result - 0.5) < 1e-9
