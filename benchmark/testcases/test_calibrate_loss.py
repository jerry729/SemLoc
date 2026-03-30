import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_loss import calibrate_loss
else:
    from programs.calibrate_loss import calibrate_loss


def test_midpoint_interpolation():
    """Interpolation at the segment midpoint should return the average of y0 and y1."""
    result = calibrate_loss(0.0, 10.0, 1.0, 20.0, 0.5)
    assert abs(result - 15.0) < 1e-9


def test_at_left_endpoint():
    """Evaluating at x0 should return y0 exactly."""
    result = calibrate_loss(2.0, 5.0, 4.0, 9.0, 2.0)
    assert abs(result - 5.0) < 1e-9


def test_at_right_endpoint():
    """Evaluating at x1 should return y1 exactly."""
    result = calibrate_loss(2.0, 5.0, 4.0, 9.0, 4.0)
    assert abs(result - 9.0) < 1e-9


def test_degenerate_segment_raises():
    """A segment with x0 == x1 must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate segment"):
        calibrate_loss(3.0, 1.0, 3.0, 2.0, 3.0)


def test_quarter_point_no_clamp():
    """At quarter-point within the segment and clamp disabled, result should be standard linear interpolation."""
    result = calibrate_loss(0.0, 0.0, 4.0, 8.0, 1.0, clamp=False)
    assert abs(result - 2.0) < 1e-9


def test_clamp_restricts_extrapolation_beyond_x1():
    """With clamping enabled, querying beyond x1 should return y1 rather than extrapolating."""
    result = calibrate_loss(0.0, 10.0, 1.0, 20.0, 2.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamp_restricts_extrapolation_before_x0():
    """With clamping enabled, querying before x0 should return y0 rather than extrapolating."""
    result = calibrate_loss(0.0, 10.0, 1.0, 20.0, -1.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamp_with_decreasing_loss():
    """Clamping should work correctly when y1 < y0 and x is beyond x1."""
    result = calibrate_loss(0.0, 20.0, 1.0, 10.0, 2.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_no_clamp_allows_extrapolation_beyond():
    """Without clamping, querying beyond x1 should freely extrapolate the line."""
    result = calibrate_loss(0.0, 10.0, 1.0, 20.0, 2.0, clamp=False)
    assert abs(result - 30.0) < 1e-9


def test_no_clamp_allows_extrapolation_before():
    """Without clamping, querying before x0 should freely extrapolate the line."""
    result = calibrate_loss(0.0, 10.0, 1.0, 20.0, -1.0, clamp=False)
    assert abs(result - 0.0) < 1e-9
