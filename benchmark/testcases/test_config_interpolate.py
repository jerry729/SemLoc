import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.config_interpolate import config_interpolate
else:
    from programs.config_interpolate import config_interpolate


def test_midpoint_interpolation():
    """A query at the exact midpoint of the domain should return the midpoint of the range."""
    result = config_interpolate(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_at_left_anchor():
    """Querying at x0 should return y0."""
    result = config_interpolate(0.0, 100.0, 1.0, 200.0, 0.0)
    assert abs(result - 100.0) < 1e-9


def test_at_right_anchor():
    """Querying at x1 should return y1."""
    result = config_interpolate(0.0, 100.0, 1.0, 200.0, 1.0)
    assert abs(result - 200.0) < 1e-9


def test_degenerate_range_raises():
    """When x0 equals x1 the domain is degenerate and must raise ValueError."""
    with pytest.raises(ValueError, match="degenerate range"):
        config_interpolate(5.0, 10.0, 5.0, 20.0, 5.0)


def test_clamped_above_upper_bound():
    """With clamping enabled, a query beyond x1 should not exceed the anchor range."""
    result = config_interpolate(0.0, 10.0, 10.0, 20.0, 15.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamped_below_lower_bound():
    """With clamping enabled, a query below x0 should not go below the anchor range."""
    result = config_interpolate(0.0, 10.0, 10.0, 20.0, -5.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamped_inverted_anchors_above():
    """Clamping should work correctly when y0 > y1 and query overshoots x1."""
    result = config_interpolate(0.0, 50.0, 10.0, 20.0, 20.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamped_inverted_anchors_below():
    """Clamping should work correctly when y0 > y1 and query undershoots x0."""
    result = config_interpolate(0.0, 50.0, 10.0, 20.0, -10.0, clamp=True)
    assert abs(result - 50.0) < 1e-9


def test_unclamped_extrapolation_above():
    """Without clamping the interpolation may extrapolate beyond the anchor range."""
    result = config_interpolate(0.0, 10.0, 10.0, 20.0, 20.0, clamp=False)
    assert abs(result - 30.0) < 1e-9


def test_unclamped_extrapolation_below():
    """Without clamping the interpolation may extrapolate below the anchor range."""
    result = config_interpolate(0.0, 10.0, 10.0, 20.0, -10.0, clamp=False)
    assert abs(result - 0.0) < 1e-9
