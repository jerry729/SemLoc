import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_quality import calibrate_quality
else:
    from programs.calibrate_quality import calibrate_quality


def test_midpoint_interpolation():
    """A query exactly at the segment midpoint should return the average quality."""
    result = calibrate_quality(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_endpoint_left():
    """Querying at the left calibration point should return y0."""
    result = calibrate_quality(0.0, 30.0, 10.0, 50.0, 0.0)
    assert abs(result - 30.0) < 1e-9


def test_endpoint_right():
    """Querying at the right calibration point should return y1."""
    result = calibrate_quality(0.0, 30.0, 10.0, 50.0, 10.0)
    assert abs(result - 50.0) < 1e-9


def test_degenerate_segment_raises():
    """A zero-length segment must raise ValueError."""
    with pytest.raises(ValueError):
        calibrate_quality(5.0, 10.0, 5.0, 20.0, 5.0)


def test_clamp_extrapolation_above():
    """With clamping enabled, querying beyond x1 should not exceed the segment quality range."""
    result = calibrate_quality(0.0, 20.0, 10.0, 40.0, 15.0, clamp=True)
    assert abs(result - 40.0) < 1e-9


def test_clamp_extrapolation_below():
    """With clamping enabled, querying below x0 should not go below the segment quality range."""
    result = calibrate_quality(0.0, 20.0, 10.0, 40.0, -5.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamp_prevents_overshoot_large_extrapolation():
    """A large overshoot beyond x1 must still be clamped to the upper calibration quality."""
    result = calibrate_quality(0.0, 10.0, 10.0, 50.0, 30.0, clamp=True)
    assert abs(result - 50.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """With clamping disabled, extrapolation beyond the segment is permitted."""
    result = calibrate_quality(0.0, 10.0, 10.0, 50.0, 20.0, clamp=False)
    assert abs(result - 90.0) < 1e-9


def test_decreasing_quality_segment_with_clamp():
    """Clamping should work correctly when y0 > y1 (decreasing quality)."""
    result = calibrate_quality(0.0, 80.0, 10.0, 40.0, 15.0, clamp=True)
    assert abs(result - 40.0) < 1e-9


def test_quarter_interpolation():
    """A query at one quarter of the segment should yield the corresponding quality."""
    result = calibrate_quality(0.0, 0.0, 100.0, 80.0, 25.0)
    assert abs(result - 20.0) < 1e-9
