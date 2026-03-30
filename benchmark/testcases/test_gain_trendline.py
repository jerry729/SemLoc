import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.gain_trendline import gain_trendline
else:
    from programs.gain_trendline import gain_trendline


def test_midpoint_interpolation():
    """Gain at the midpoint of a segment should be the average of endpoints."""
    result = gain_trendline(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_at_first_control_point():
    """Gain at the first control point must equal y0."""
    result = gain_trendline(0.0, -3.0, 4.0, 5.0, 0.0)
    assert abs(result - (-3.0)) < 1e-9


def test_at_second_control_point():
    """Gain at the second control point must equal y1."""
    result = gain_trendline(1.0, 2.0, 5.0, 10.0, 5.0)
    assert abs(result - 10.0) < 1e-9


def test_degenerate_segment_raises():
    """A segment with zero length must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate"):
        gain_trendline(3.0, 1.0, 3.0, 2.0, 3.0)


def test_quarter_interpolation():
    """Gain at one-quarter of the segment follows linear proportion."""
    result = gain_trendline(0.0, 0.0, 8.0, 40.0, 2.0)
    assert abs(result - 10.0) < 1e-9


def test_clamped_above_segment():
    """When querying beyond x1 with clamping, gain must not exceed y1."""
    result = gain_trendline(0.0, 0.0, 10.0, 20.0, 15.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamped_below_segment():
    """When querying before x0 with clamping, gain must not go below y0."""
    result = gain_trendline(2.0, 5.0, 6.0, 25.0, -2.0, clamp=True)
    assert abs(result - 5.0) < 1e-9


def test_clamped_decreasing_segment_above():
    """Clamping on a decreasing segment beyond x1 limits to the lower endpoint."""
    result = gain_trendline(0.0, 30.0, 10.0, 10.0, 20.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamped_decreasing_segment_below():
    """Clamping on a decreasing segment before x0 limits to the upper endpoint."""
    result = gain_trendline(0.0, 30.0, 10.0, 10.0, -5.0, clamp=True)
    assert abs(result - 30.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """Without clamping the result should follow the linear extension."""
    result = gain_trendline(0.0, 0.0, 10.0, 20.0, 15.0, clamp=False)
    assert abs(result - 30.0) < 1e-9
