import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_score import calibrate_score
else:
    from programs.calibrate_score import calibrate_score


def test_midpoint_interpolation():
    """A query at the midpoint of the segment should return the average of the two anchor scores."""
    result = calibrate_score(0.0, 0.0, 1.0, 1.0, 0.5)
    assert abs(result - 0.5) < 1e-9


def test_exact_left_anchor():
    """Querying at x0 should return exactly y0."""
    result = calibrate_score(2.0, 10.0, 4.0, 20.0, 2.0)
    assert abs(result - 10.0) < 1e-9


def test_exact_right_anchor():
    """Querying at x1 should return exactly y1."""
    result = calibrate_score(2.0, 10.0, 4.0, 20.0, 4.0)
    assert abs(result - 20.0) < 1e-9


def test_degenerate_segment_raises():
    """A segment with identical x-coordinates must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate segment"):
        calibrate_score(5.0, 0.0, 5.0, 1.0, 5.0)


def test_clamp_above_upper_bound():
    """With clamping enabled, extrapolating beyond x1 should cap the score at y1."""
    result = calibrate_score(0.0, 0.0, 1.0, 1.0, 2.0, clamp=True)
    assert abs(result - 1.0) < 1e-9


def test_clamp_below_lower_bound():
    """With clamping enabled, extrapolating below x0 should cap the score at y0."""
    result = calibrate_score(0.0, 0.0, 1.0, 1.0, -1.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """With clamping disabled, the function should extrapolate beyond anchor bounds."""
    result = calibrate_score(0.0, 0.0, 1.0, 1.0, 2.0, clamp=False)
    assert abs(result - 2.0) < 1e-9


def test_clamp_decreasing_segment_above():
    """On a decreasing segment, clamping beyond x1 should return the lower score y1."""
    result = calibrate_score(0.0, 10.0, 1.0, 5.0, 3.0, clamp=True)
    assert abs(result - 5.0) < 1e-9


def test_clamp_decreasing_segment_below():
    """On a decreasing segment, clamping before x0 should return y0."""
    result = calibrate_score(0.0, 10.0, 1.0, 5.0, -2.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_no_clamp_negative_extrapolation():
    """With clamping disabled, extrapolating below x0 should give an unconstrained linear value."""
    result = calibrate_score(0.0, 0.0, 1.0, 1.0, -0.5, clamp=False)
    assert abs(result - (-0.5)) < 1e-9
