import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.confidence_trendline import confidence_trendline
else:
    from programs.confidence_trendline import confidence_trendline


def test_midpoint_interpolation():
    """Interpolating at the midpoint should return the average of the two confidence values."""
    result = confidence_trendline(0.0, 0.2, 10.0, 0.8, 5.0)
    assert abs(result - 0.5) < 1e-9


def test_at_first_reference_point():
    """Evaluating at x0 should return y0 exactly."""
    result = confidence_trendline(1.0, 0.3, 5.0, 0.7, 1.0)
    assert abs(result - 0.3) < 1e-9


def test_at_second_reference_point():
    """Evaluating at x1 should return y1 exactly."""
    result = confidence_trendline(1.0, 0.3, 5.0, 0.7, 5.0)
    assert abs(result - 0.7) < 1e-9


def test_equal_x_raises_error():
    """Degenerate reference points with identical x must raise ValueError."""
    with pytest.raises(ValueError):
        confidence_trendline(3.0, 0.5, 3.0, 0.9, 3.0)


def test_extrapolation_clamped_above():
    """When clamping is enabled, extrapolation above the range should be capped at max(y0, y1)."""
    result = confidence_trendline(0.0, 0.2, 1.0, 0.6, 5.0, clamp=True)
    assert abs(result - 0.6) < 1e-9


def test_extrapolation_clamped_below():
    """When clamping is enabled, extrapolation below the range should be floored at min(y0, y1)."""
    result = confidence_trendline(0.0, 0.2, 1.0, 0.6, -5.0, clamp=True)
    assert abs(result - 0.2) < 1e-9


def test_extrapolation_unclamped():
    """When clamping is disabled, extrapolation should return the raw linear value."""
    result = confidence_trendline(0.0, 0.2, 1.0, 0.6, 2.0, clamp=False)
    assert abs(result - 1.0) < 1e-9


def test_clamp_prevents_exceeding_upper_bound():
    """Clamped confidence should not exceed the larger of the two reference values."""
    result = confidence_trendline(0.0, 0.3, 1.0, 0.7, 10.0, clamp=True)
    assert result <= 0.7 + 1e-9


def test_clamp_prevents_going_below_lower_bound():
    """Clamped confidence should not fall below the smaller of the two reference values."""
    result = confidence_trendline(0.0, 0.3, 1.0, 0.7, -10.0, clamp=True)
    assert result >= 0.3 - 1e-9


def test_no_clamp_allows_negative_extrapolation():
    """Without clamping, extrapolation may yield values below both reference confidences."""
    result = confidence_trendline(0.0, 0.5, 1.0, 0.8, -3.0, clamp=False)
    expected = 0.5 + (-3.0) * (0.8 - 0.5)
    assert abs(result - max(0.0, expected)) < 1e-9
