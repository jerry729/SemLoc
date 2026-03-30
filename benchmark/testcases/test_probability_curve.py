import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.probability_curve import probability_curve
else:
    from programs.probability_curve import probability_curve


def test_midpoint_interpolation():
    """Evaluating at the segment midpoint should return the average probability."""
    result = probability_curve(0.0, 0.2, 10.0, 0.8, 5.0)
    assert abs(result - 0.5) < 1e-9


def test_at_left_anchor():
    """Evaluating exactly at x0 must return y0."""
    result = probability_curve(1.0, 0.1, 5.0, 0.9, 1.0)
    assert abs(result - 0.1) < 1e-9


def test_at_right_anchor():
    """Evaluating exactly at x1 must return y1."""
    result = probability_curve(1.0, 0.1, 5.0, 0.9, 5.0)
    assert abs(result - 0.9) < 1e-9


def test_degenerate_segment_raises():
    """A segment with identical x-coordinates is degenerate and must raise."""
    with pytest.raises(ValueError, match="degenerate"):
        probability_curve(3.0, 0.2, 3.0, 0.8, 3.0)


def test_quarter_interpolation():
    """Evaluating at one quarter of the segment length returns proportional probability."""
    result = probability_curve(0.0, 0.0, 100.0, 1.0, 25.0)
    assert abs(result - 0.25) < 1e-9


def test_clamp_above_right_anchor():
    """When x exceeds x1 with clamping enabled, the result must not exceed y1."""
    result = probability_curve(0.0, 0.2, 10.0, 0.8, 20.0)
    assert abs(result - 0.8) < 1e-9


def test_clamp_below_left_anchor():
    """When x is below x0 with clamping enabled, the result must not drop below y0."""
    result = probability_curve(0.0, 0.2, 10.0, 0.8, -5.0)
    assert abs(result - 0.2) < 1e-9


def test_no_clamp_extrapolation_above():
    """With clamping enabled, extrapolation beyond the segment should be bounded."""
    result = probability_curve(0.0, 0.0, 10.0, 0.5, 15.0, clamp=True)
    assert abs(result - 0.5) < 1e-9


def test_no_clamp_extrapolation_below():
    """With clamping enabled, extrapolation below the segment should be bounded."""
    result = probability_curve(0.0, 0.3, 10.0, 0.7, -10.0, clamp=True)
    assert abs(result - 0.3) < 1e-9


def test_decreasing_segment_clamp():
    """Clamping on a decreasing segment should still restrict to anchor range."""
    result = probability_curve(0.0, 0.9, 10.0, 0.1, 15.0, clamp=True)
    assert abs(result - 0.1) < 1e-9
