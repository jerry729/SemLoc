import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.demand_curve import demand_curve
else:
    from programs.demand_curve import demand_curve


def test_midpoint_interpolation():
    """Demand at the midpoint of a segment should equal the average of the endpoints."""
    result = demand_curve(0.0, 100.0, 10.0, 200.0, 5.0)
    assert abs(result - 150.0) < 1e-9


def test_at_left_endpoint():
    """Querying exactly at the left endpoint should return y0."""
    result = demand_curve(2.0, 50.0, 8.0, 80.0, 2.0)
    assert abs(result - 50.0) < 1e-9


def test_at_right_endpoint():
    """Querying exactly at the right endpoint should return y1."""
    result = demand_curve(2.0, 50.0, 8.0, 80.0, 8.0)
    assert abs(result - 80.0) < 1e-9


def test_zero_length_segment_raises():
    """A degenerate segment with x0 == x1 must raise ValueError."""
    with pytest.raises(ValueError, match="zero length"):
        demand_curve(5.0, 10.0, 5.0, 20.0, 5.0)


def test_unclamped_within_segment():
    """Without clamping, a query inside the segment should still interpolate correctly."""
    result = demand_curve(0.0, 0.0, 10.0, 100.0, 3.0, clamp=False)
    assert abs(result - 30.0) < 1e-9


def test_clamped_beyond_right_endpoint():
    """Demand should not exceed y1 when querying past the right endpoint with clamping."""
    result = demand_curve(0.0, 100.0, 10.0, 200.0, 20.0)
    assert abs(result - 200.0) < 1e-9


def test_clamped_beyond_left_endpoint():
    """Demand should not drop below y0 when querying before the left endpoint with clamping."""
    result = demand_curve(0.0, 100.0, 10.0, 200.0, -5.0)
    assert abs(result - 100.0) < 1e-9


def test_clamped_far_extrapolation_decreasing():
    """For a decreasing segment, clamping should cap demand at y1 when x >> x1."""
    result = demand_curve(0.0, 200.0, 10.0, 50.0, 30.0)
    assert abs(result - 50.0) < 1e-9


def test_clamped_negative_direction_extrapolation():
    """Querying far left on an increasing segment should clamp demand at y0."""
    result = demand_curve(10.0, 20.0, 20.0, 80.0, -10.0)
    assert abs(result - 20.0) < 1e-9


def test_clamp_default_is_true():
    """The default behavior should apply clamping, preventing extrapolation."""
    clamped = demand_curve(0.0, 0.0, 10.0, 100.0, 15.0)
    unclamped = demand_curve(0.0, 0.0, 10.0, 100.0, 15.0, clamp=False)
    assert abs(clamped - 100.0) < 1e-9
    assert abs(unclamped - 150.0) < 1e-9
