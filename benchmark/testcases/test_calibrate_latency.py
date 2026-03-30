import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_latency import calibrate_latency
else:
    from programs.calibrate_latency import calibrate_latency


def test_midpoint_interpolation():
    """Midpoint of the segment should return the average of the two latencies."""
    result = calibrate_latency(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_at_first_endpoint():
    """Query at the first calibration point returns its latency exactly."""
    result = calibrate_latency(0.0, 100.0, 10.0, 200.0, 0.0)
    assert abs(result - 100.0) < 1e-9


def test_at_second_endpoint():
    """Query at the second calibration point returns its latency exactly."""
    result = calibrate_latency(0.0, 100.0, 10.0, 200.0, 10.0)
    assert abs(result - 200.0) < 1e-9


def test_zero_length_segment_raises():
    """A degenerate segment with equal x-coordinates must raise ValueError."""
    with pytest.raises(ValueError, match="zero length"):
        calibrate_latency(5.0, 10.0, 5.0, 20.0, 5.0)


def test_unclamped_within_range():
    """When clamp is disabled and x is inside the segment, interpolation is linear."""
    result = calibrate_latency(0.0, 10.0, 10.0, 30.0, 5.0, clamp=False)
    assert abs(result - 20.0) < 1e-9


def test_clamped_extrapolation_above():
    """With clamping enabled, querying beyond x1 should not exceed the y1 bound."""
    result = calibrate_latency(0.0, 10.0, 10.0, 20.0, 20.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamped_extrapolation_below():
    """With clamping enabled, querying before x0 should not go below the y0 bound."""
    result = calibrate_latency(0.0, 10.0, 10.0, 20.0, -10.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamped_extrapolation_below_reversed_latencies():
    """Clamping should hold when y0 > y1 and x is below x0."""
    result = calibrate_latency(0.0, 50.0, 10.0, 20.0, -10.0, clamp=True)
    assert abs(result - 50.0) < 1e-9


def test_clamped_extrapolation_above_reversed_latencies():
    """Clamping should hold when y0 > y1 and x is above x1."""
    result = calibrate_latency(0.0, 50.0, 10.0, 20.0, 20.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_unclamped_allows_extrapolation():
    """Without clamping, the result should extrapolate linearly beyond the segment."""
    result = calibrate_latency(0.0, 10.0, 10.0, 20.0, 20.0, clamp=False)
    assert abs(result - 30.0) < 1e-9
