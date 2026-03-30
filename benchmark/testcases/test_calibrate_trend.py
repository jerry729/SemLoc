import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.calibrate_trend import calibrate_trend
else:
    from programs.calibrate_trend import calibrate_trend


def test_midpoint_interpolation():
    """Querying the exact midpoint of the segment should return the average of the endpoints."""
    result = calibrate_trend(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_at_start_point():
    """Querying at x0 should return y0 regardless of clamping."""
    result = calibrate_trend(1.0, 100.0, 5.0, 200.0, 1.0)
    assert abs(result - 100.0) < 1e-9


def test_at_end_point():
    """Querying at x1 should return y1 regardless of clamping."""
    result = calibrate_trend(1.0, 100.0, 5.0, 200.0, 5.0)
    assert abs(result - 200.0) < 1e-9


def test_zero_length_raises():
    """A degenerate segment with identical x-values must raise ValueError."""
    with pytest.raises(ValueError, match="zero length"):
        calibrate_trend(3.0, 10.0, 3.0, 20.0, 3.0)


def test_clamp_prevents_extrapolation_above():
    """With clamping enabled, querying beyond x1 should not exceed y1."""
    result = calibrate_trend(0.0, 0.0, 10.0, 100.0, 20.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_clamp_prevents_extrapolation_below():
    """With clamping enabled, querying below x0 should not go below y0."""
    result = calibrate_trend(0.0, 0.0, 10.0, 100.0, -5.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_clamp_with_decreasing_trend_above():
    """Clamping on a decreasing segment should cap the value at y1 when x > x1."""
    result = calibrate_trend(0.0, 100.0, 10.0, 0.0, 15.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_clamp_with_decreasing_trend_below():
    """Clamping on a decreasing segment should cap the value at y0 when x < x0."""
    result = calibrate_trend(0.0, 100.0, 10.0, 0.0, -5.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """With clamping disabled, extrapolation beyond the segment is permitted."""
    result = calibrate_trend(0.0, 0.0, 10.0, 100.0, 20.0, clamp=False)
    assert abs(result - 200.0) < 1e-9


def test_quarter_interpolation():
    """Querying at 25%% of the segment should return the corresponding linear value."""
    result = calibrate_trend(0.0, 0.0, 8.0, 80.0, 2.0)
    assert abs(result - 20.0) < 1e-9
