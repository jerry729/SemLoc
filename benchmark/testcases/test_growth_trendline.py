import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.growth_trendline import growth_trendline
else:
    from programs.growth_trendline import growth_trendline


def test_midpoint_interpolation():
    """The midpoint of a growth segment should return the average of the endpoints."""
    result = growth_trendline(0.0, 100.0, 10.0, 200.0, 5.0)
    assert abs(result - 150.0) < 1e-9


def test_at_left_endpoint():
    """Querying at x0 should return y0 exactly."""
    result = growth_trendline(2.0, 50.0, 8.0, 110.0, 2.0)
    assert abs(result - 50.0) < 1e-9


def test_at_right_endpoint():
    """Querying at x1 should return y1 exactly."""
    result = growth_trendline(2.0, 50.0, 8.0, 110.0, 8.0)
    assert abs(result - 110.0) < 1e-9


def test_degenerate_segment_raises():
    """A degenerate segment (x0 == x1) must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate segment"):
        growth_trendline(5.0, 10.0, 5.0, 20.0, 5.0)


def test_clamped_above_right_endpoint():
    """When clamped, querying beyond x1 should not exceed y1."""
    result = growth_trendline(0.0, 100.0, 10.0, 200.0, 15.0, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamped_below_left_endpoint():
    """When clamped, querying before x0 should not go below y0."""
    result = growth_trendline(0.0, 100.0, 10.0, 200.0, -5.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_unclamped_extrapolation_above():
    """Without clamping, extrapolation beyond x1 should follow the line."""
    result = growth_trendline(0.0, 100.0, 10.0, 200.0, 20.0, clamp=False)
    assert abs(result - 300.0) < 1e-9


def test_unclamped_extrapolation_below():
    """Without clamping, extrapolation before x0 should follow the line."""
    result = growth_trendline(0.0, 100.0, 10.0, 200.0, -10.0, clamp=False)
    assert abs(result - 0.0) < 1e-9


def test_clamped_decreasing_segment():
    """Clamping on a decreasing segment must still restrict to the corridor."""
    result = growth_trendline(0.0, 200.0, 10.0, 100.0, 15.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_clamped_quarter_interpolation():
    """Quarter-way through the segment should yield a proportional value."""
    result = growth_trendline(0.0, 0.0, 100.0, 400.0, 25.0, clamp=True)
    assert abs(result - 100.0) < 1e-9
