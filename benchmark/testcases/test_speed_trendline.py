import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.speed_trendline import speed_trendline
else:
    from programs.speed_trendline import speed_trendline


def test_midpoint_interpolation():
    """Speed at the midpoint of two reference positions equals the average of the two speeds."""
    result = speed_trendline(0.0, 60.0, 10.0, 80.0, 5.0)
    assert abs(result - 70.0) < 1e-9


def test_at_first_reference_point():
    """Querying at x0 must return the speed y0."""
    result = speed_trendline(0.0, 50.0, 100.0, 100.0, 0.0)
    assert abs(result - 50.0) < 1e-9


def test_at_second_reference_point():
    """Querying at x1 must return the speed y1."""
    result = speed_trendline(0.0, 50.0, 100.0, 100.0, 100.0)
    assert abs(result - 100.0) < 1e-9


def test_equal_positions_raises():
    """When both reference positions are identical, a ValueError must be raised."""
    with pytest.raises(ValueError):
        speed_trendline(5.0, 40.0, 5.0, 80.0, 5.0)


def test_extrapolation_clamped_above():
    """When x is beyond the reference interval with clamp=True, speed must not exceed max(y0, y1)."""
    result = speed_trendline(0.0, 60.0, 10.0, 80.0, 20.0, clamp=True)
    assert abs(result - 80.0) < 1e-9


def test_extrapolation_clamped_below():
    """When x is before the reference interval with clamp=True, speed must not drop below min(y0, y1)."""
    result = speed_trendline(0.0, 60.0, 10.0, 80.0, -10.0, clamp=True)
    assert abs(result - 60.0) < 1e-9


def test_no_clamp_allows_extrapolation_above():
    """With clamping disabled, extrapolation beyond the segment should yield unconstrained values."""
    result = speed_trendline(0.0, 60.0, 10.0, 80.0, 20.0, clamp=False)
    assert abs(result - 100.0) < 1e-9


def test_no_clamp_allows_extrapolation_below():
    """With clamping disabled, extrapolation before the segment should yield unconstrained values."""
    result = speed_trendline(0.0, 60.0, 10.0, 80.0, -10.0, clamp=False)
    assert abs(result - 40.0) < 1e-9


def test_decreasing_speed_clamped_above():
    """For a decreasing speed profile, querying before x0 with clamp should cap at y0."""
    result = speed_trendline(0.0, 100.0, 10.0, 60.0, -5.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_decreasing_speed_clamped_below():
    """For a decreasing speed profile, querying past x1 with clamp should cap at y1."""
    result = speed_trendline(0.0, 100.0, 10.0, 60.0, 20.0, clamp=True)
    assert abs(result - 60.0) < 1e-9
