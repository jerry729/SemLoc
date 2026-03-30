import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.estimate_supply import estimate_supply
else:
    from programs.estimate_supply import estimate_supply


def test_midpoint_interpolation():
    """Supply at the midpoint of a segment equals the average of the endpoints."""
    result = estimate_supply(0.0, 100.0, 10.0, 200.0, 5.0)
    assert abs(result - 150.0) < 1e-9


def test_at_start_endpoint():
    """Supply at the start station equals the start measurement."""
    result = estimate_supply(0.0, 50.0, 10.0, 150.0, 0.0)
    assert abs(result - 50.0) < 1e-9


def test_at_end_endpoint():
    """Supply at the end station equals the end measurement."""
    result = estimate_supply(0.0, 50.0, 10.0, 150.0, 10.0)
    assert abs(result - 150.0) < 1e-9


def test_degenerate_segment_raises():
    """A zero-length segment must raise ValueError."""
    with pytest.raises(ValueError):
        estimate_supply(5.0, 100.0, 5.0, 200.0, 5.0)


def test_quarter_position():
    """Supply at 25 percent along the segment should be linearly proportional."""
    result = estimate_supply(0.0, 0.0, 100.0, 400.0, 25.0)
    assert abs(result - 100.0) < 1e-9


def test_clamped_beyond_upper_endpoint():
    """When query exceeds the segment range, clamped output must not exceed the endpoint supply."""
    result = estimate_supply(0.0, 100.0, 10.0, 200.0, 20.0, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamped_below_lower_endpoint():
    """When query is before the segment, clamped output must not go below the start supply."""
    result = estimate_supply(0.0, 100.0, 10.0, 200.0, -5.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_clamp_default_restricts_extrapolation():
    """Default clamping should restrict supply to the segment range for out-of-bound queries."""
    result = estimate_supply(2.0, 10.0, 4.0, 20.0, 6.0)
    assert abs(result - 20.0) < 1e-9


def test_clamp_false_allows_extrapolation_below():
    """With clamping disabled, extrapolation below the segment should be unrestricted."""
    result = estimate_supply(0.0, 100.0, 10.0, 200.0, -10.0, clamp=False)
    assert abs(result - 0.0) < 1e-9


def test_decreasing_supply_clamp_above():
    """For a decreasing supply segment, clamping must restrict the upper bound correctly."""
    result = estimate_supply(0.0, 200.0, 10.0, 100.0, 15.0, clamp=True)
    assert abs(result - 100.0) < 1e-9
