import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_lift import calibrate_lift
else:
    from programs.calibrate_lift import calibrate_lift


def test_clamp_extrapolation_beyond_x1():
    """When clamp=True, querying beyond x1 should return y1 (clamped to segment endpoint)."""
    result = calibrate_lift(0.0, 0.0, 1.0, 10.0, 2.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamp_extrapolation_below_x0():
    """When clamp=True, querying below x0 should return y0 (clamped to segment endpoint)."""
    result = calibrate_lift(0.0, 0.0, 1.0, 10.0, -1.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_clamp_extrapolation_beyond_with_decreasing_y():
    """When clamp=True and y1 < y0, querying beyond x1 should return y1."""
    result = calibrate_lift(0.0, 10.0, 1.0, 0.0, 3.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_clamp_extrapolation_below_with_decreasing_y():
    """When clamp=True and y1 < y0, querying below x0 should return y0."""
    result = calibrate_lift(0.0, 10.0, 1.0, 0.0, -2.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_no_clamp_allows_extrapolation_beyond():
    """When clamp=False, querying beyond x1 should extrapolate freely."""
    result = calibrate_lift(0.0, 0.0, 1.0, 10.0, 2.0, clamp=False)
    assert abs(result - 20.0) < 1e-9


def test_no_clamp_allows_extrapolation_below():
    """When clamp=False, querying below x0 should extrapolate freely."""
    result = calibrate_lift(0.0, 0.0, 1.0, 10.0, -1.0, clamp=False)
    assert abs(result - (-10.0)) < 1e-9


def test_interpolation_midpoint():
    """Querying at the midpoint of the segment should return the average of y0 and y1."""
    result = calibrate_lift(0.0, 0.0, 1.0, 10.0, 0.5, clamp=True)
    assert abs(result - 5.0) < 1e-9


def test_interpolation_at_endpoints():
    """Querying at x0 should return y0, and at x1 should return y1."""
    result_x0 = calibrate_lift(0.0, 2.0, 4.0, 6.0, 0.0, clamp=True)
    result_x1 = calibrate_lift(0.0, 2.0, 4.0, 6.0, 4.0, clamp=True)
    assert abs(result_x0 - 2.0) < 1e-9
    assert abs(result_x1 - 6.0) < 1e-9


def test_zero_length_segment_raises():
    """A degenerate segment where x0 == x1 should raise ValueError."""
    with pytest.raises(ValueError, match="zero length"):
        calibrate_lift(5.0, 1.0, 5.0, 3.0, 5.0)


def test_clamp_at_exact_boundary_x_equals_x1():
    """When x equals x1 exactly with clamp=True, result should be y1 without clamping distortion."""
    result = calibrate_lift(2.0, 3.0, 5.0, 9.0, 5.0, clamp=True)
    assert abs(result - 9.0) < 1e-9