import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.demand_forecast_curve import demand_forecast_curve
else:
    from programs.demand_forecast_curve import demand_forecast_curve


def test_midpoint_interpolation():
    """Querying exactly between two anchors should return the average demand."""
    result = demand_forecast_curve(0, 100, 10, 200, 5)
    assert abs(result - 150.0) < 1e-9


def test_at_first_anchor():
    """Querying at x0 should return y0 exactly."""
    result = demand_forecast_curve(1, 50, 5, 150, 1)
    assert abs(result - 50.0) < 1e-9


def test_at_second_anchor():
    """Querying at x1 should return y1 exactly."""
    result = demand_forecast_curve(1, 50, 5, 150, 5)
    assert abs(result - 150.0) < 1e-9


def test_identical_anchors_raise():
    """Degenerate segment with x0 == x1 must raise ValueError."""
    with pytest.raises(ValueError):
        demand_forecast_curve(3, 10, 3, 20, 3)


def test_clamp_upper_bound():
    """Extrapolation beyond the higher anchor should be clamped to max(y0, y1)."""
    result = demand_forecast_curve(0, 100, 10, 200, 20, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamp_lower_bound():
    """Extrapolation below the lower anchor should be clamped to min(y0, y1)."""
    result = demand_forecast_curve(0, 100, 10, 200, -5, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_no_clamp_allows_extrapolation_above():
    """With clamping disabled, forecasts above the anchor range are permitted."""
    result = demand_forecast_curve(0, 100, 10, 200, 20, clamp=False)
    assert abs(result - 300.0) < 1e-9


def test_no_clamp_allows_extrapolation_below():
    """With clamping disabled, forecasts below the anchor range are permitted."""
    result = demand_forecast_curve(0, 100, 10, 200, -5, clamp=False)
    assert abs(result - 50.0) < 1e-9


def test_clamp_descending_segment_upper():
    """On a descending demand curve, clamping should still cap at the higher value."""
    result = demand_forecast_curve(0, 200, 10, 100, -5, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamp_descending_segment_lower():
    """On a descending demand curve, clamping should still floor at the lower value."""
    result = demand_forecast_curve(0, 200, 10, 100, 15, clamp=True)
    assert abs(result - 100.0) < 1e-9
