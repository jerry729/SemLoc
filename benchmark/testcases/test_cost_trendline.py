import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.cost_trendline import cost_trendline
else:
    from programs.cost_trendline import cost_trendline


def test_midpoint_interpolation():
    """Querying the midpoint between two anchors returns the average cost."""
    result = cost_trendline(0, 100, 10, 200, 5)
    assert abs(result - 150.0) < 1e-9


def test_at_first_anchor():
    """Querying at x0 returns the first anchor cost exactly."""
    result = cost_trendline(0, 50, 10, 150, 0)
    assert abs(result - 50.0) < 1e-9


def test_at_second_anchor():
    """Querying at x1 returns the second anchor cost exactly."""
    result = cost_trendline(0, 50, 10, 150, 10)
    assert abs(result - 150.0) < 1e-9


def test_equal_x_raises_value_error():
    """Degenerate anchor points with equal x-coordinates must raise ValueError."""
    with pytest.raises(ValueError):
        cost_trendline(5, 100, 5, 200, 5)


def test_negative_slope_midpoint():
    """Decreasing cost trendline returns correct midpoint value."""
    result = cost_trendline(0, 200, 10, 100, 5)
    assert abs(result - 150.0) < 1e-9


def test_clamp_prevents_extrapolation_above():
    """When clamping is enabled, extrapolation beyond the upper anchor is capped."""
    result = cost_trendline(0, 100, 10, 200, 20, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamp_prevents_extrapolation_below():
    """When clamping is enabled, extrapolation below the lower anchor is floored."""
    result = cost_trendline(0, 100, 10, 200, -5, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """When clamping is disabled, the raw extrapolated value is returned."""
    result = cost_trendline(0, 100, 10, 200, 20, clamp=False)
    assert abs(result - 300.0) < 1e-9


def test_clamp_default_enabled_caps_high():
    """Default clamping behaviour should cap values that exceed the anchor range."""
    result = cost_trendline(0, 0, 10, 100, 15)
    assert abs(result - 100.0) < 1e-9


def test_clamp_default_enabled_caps_low():
    """Default clamping behaviour should floor values below the anchor range."""
    result = cost_trendline(0, 0, 10, 100, -3)
    assert abs(result - 0.0) < 1e-9
