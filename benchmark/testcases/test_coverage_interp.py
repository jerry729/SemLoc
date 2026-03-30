import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.coverage_interp import coverage_interp
else:
    from programs.coverage_interp import coverage_interp


def test_midpoint_interpolation():
    """Querying the midpoint of a segment should return the average of the two coverage values."""
    result = coverage_interp(0.0, 0.0, 10.0, 1.0, 5.0)
    assert abs(result - 0.5) < 1e-9


def test_interpolation_at_left_endpoint():
    """Querying exactly at the left endpoint should return y0."""
    result = coverage_interp(2.0, 0.3, 8.0, 0.9, 2.0)
    assert abs(result - 0.3) < 1e-9


def test_interpolation_at_right_endpoint():
    """Querying exactly at the right endpoint should return y1."""
    result = coverage_interp(2.0, 0.3, 8.0, 0.9, 8.0)
    assert abs(result - 0.9) < 1e-9


def test_degenerate_segment_raises():
    """A degenerate segment (x0 == x1) must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate segment"):
        coverage_interp(5.0, 0.2, 5.0, 0.8, 5.0)


def test_clamp_extrapolation_beyond_right():
    """With clamping enabled, querying beyond the right endpoint should not extrapolate past y1."""
    result = coverage_interp(0.0, 0.0, 10.0, 1.0, 20.0, clamp=True)
    assert abs(result - 1.0) < 1e-9


def test_clamp_extrapolation_beyond_left():
    """With clamping enabled, querying before the left endpoint should not extrapolate below y0."""
    result = coverage_interp(0.0, 0.0, 10.0, 1.0, -5.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_no_clamp_allows_extrapolation_right():
    """Without clamping, querying beyond the segment should yield the unclamped linear extrapolation."""
    result = coverage_interp(0.0, 0.0, 10.0, 1.0, 20.0, clamp=False)
    assert abs(result - 2.0) < 1e-9


def test_no_clamp_allows_extrapolation_left():
    """Without clamping, querying before the segment should yield the unclamped linear extrapolation."""
    result = coverage_interp(0.0, 0.0, 10.0, 1.0, -5.0, clamp=False)
    assert abs(result - (-0.5)) < 1e-9


def test_clamp_decreasing_segment():
    """With clamping on a decreasing segment, extrapolation past the right end should stay at y1."""
    result = coverage_interp(0.0, 1.0, 10.0, 0.0, 15.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_quarter_point_interpolation():
    """Querying at 25% of the segment should return the quarter-weighted coverage."""
    result = coverage_interp(0.0, 2.0, 4.0, 6.0, 1.0)
    assert abs(result - 3.0) < 1e-9
