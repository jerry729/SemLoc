import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.estimate_temperature import estimate_temperature
else:
    from programs.estimate_temperature import estimate_temperature


def test_midpoint_interpolation():
    """Temperature at the midpoint of two sensors should be the average of their readings."""
    result = estimate_temperature(0.0, 100.0, 10.0, 200.0, 5.0)
    assert abs(result - 150.0) < 1e-9


def test_at_left_endpoint():
    """Temperature at the left sensor position should equal y0."""
    result = estimate_temperature(0.0, 20.0, 10.0, 80.0, 0.0)
    assert abs(result - 20.0) < 1e-9


def test_at_right_endpoint():
    """Temperature at the right sensor position should equal y1."""
    result = estimate_temperature(0.0, 20.0, 10.0, 80.0, 10.0)
    assert abs(result - 80.0) < 1e-9


def test_zero_length_segment_raises():
    """A zero-length segment (x0 == x1) is physically meaningless and should raise."""
    with pytest.raises(ValueError, match="zero length"):
        estimate_temperature(5.0, 100.0, 5.0, 200.0, 5.0)


def test_quarter_position_no_clamp():
    """Interpolation at 25% position without clamping should yield the correct linear value."""
    result = estimate_temperature(0.0, 0.0, 100.0, 400.0, 25.0, clamp=False)
    assert abs(result - 100.0) < 1e-9


def test_clamp_prevents_extrapolation_above():
    """When x exceeds x1, clamping should restrict the result to y1."""
    result = estimate_temperature(0.0, 100.0, 10.0, 200.0, 20.0, clamp=True)
    assert abs(result - 200.0) < 1e-9


def test_clamp_prevents_extrapolation_below():
    """When x is below x0, clamping should restrict the result to y0."""
    result = estimate_temperature(0.0, 100.0, 10.0, 200.0, -5.0, clamp=True)
    assert abs(result - 100.0) < 1e-9


def test_extrapolation_above_with_clamp_enabled():
    """Extrapolating beyond the segment should be prevented when clamping is on."""
    result = estimate_temperature(0.0, 50.0, 10.0, 150.0, 15.0, clamp=True)
    assert abs(result - 150.0) < 1e-9


def test_extrapolation_below_with_clamp_enabled():
    """Extrapolating before the segment start should be prevented when clamping is on."""
    result = estimate_temperature(2.0, 30.0, 8.0, 90.0, -4.0, clamp=True)
    assert abs(result - 30.0) < 1e-9


def test_decreasing_temperature_clamp_above():
    """For a decreasing temperature gradient, clamping above should cap at the higher reading (y0)."""
    result = estimate_temperature(0.0, 200.0, 10.0, 100.0, -5.0, clamp=True)
    assert abs(result - 200.0) < 1e-9
