import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.model_confidence_clamp import model_confidence_clamp
else:
    from programs.model_confidence_clamp import model_confidence_clamp


def test_midpoint_interpolation():
    """Confidence at the midpoint of two anchors should be their average."""
    result = model_confidence_clamp(0.0, 0.0, 1.0, 1.0, 0.5)
    assert abs(result - 0.5) < 1e-9


def test_at_left_anchor():
    """Querying exactly at x0 should return y0."""
    result = model_confidence_clamp(0.0, 0.2, 1.0, 0.8, 0.0)
    assert abs(result - 0.2) < 1e-9


def test_at_right_anchor():
    """Querying exactly at x1 should return y1."""
    result = model_confidence_clamp(0.0, 0.2, 1.0, 0.8, 1.0)
    assert abs(result - 0.8) < 1e-9


def test_degenerate_segment_raises():
    """A segment where x0 == x1 is degenerate and must be rejected."""
    with pytest.raises(ValueError, match="degenerate segment"):
        model_confidence_clamp(5.0, 0.0, 5.0, 1.0, 5.0)


def test_clamp_above_upper_bound():
    """When clamp is enabled, extrapolation above the anchor range must be capped."""
    result = model_confidence_clamp(0.0, 0.0, 1.0, 1.0, 2.0, clamp=True)
    assert abs(result - 1.0) < 1e-9


def test_clamp_below_lower_bound():
    """When clamp is enabled, extrapolation below the anchor range must be capped."""
    result = model_confidence_clamp(0.0, 0.0, 1.0, 1.0, -1.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_no_clamp_allows_extrapolation():
    """With clamping disabled, values outside the anchor range should be returned as-is."""
    result = model_confidence_clamp(0.0, 0.0, 1.0, 1.0, 2.0, clamp=False)
    assert abs(result - 2.0) < 1e-9


def test_clamp_with_decreasing_confidence():
    """Clamping must work correctly when y0 > y1 (decreasing confidence segment)."""
    result = model_confidence_clamp(0.0, 1.0, 1.0, 0.0, 2.0, clamp=True)
    assert abs(result - 0.0) < 1e-9


def test_clamp_negative_extrapolation_decreasing():
    """Clamping below the lower anchor in a decreasing segment caps at y1."""
    result = model_confidence_clamp(0.0, 1.0, 1.0, 0.0, -1.0, clamp=True)
    assert abs(result - 1.0) < 1e-9


def test_no_clamp_negative_extrapolation():
    """Without clamping, negative-side extrapolation should yield the raw linear value."""
    result = model_confidence_clamp(0.0, 0.0, 1.0, 1.0, -0.5, clamp=False)
    assert abs(result - (-0.5)) < 1e-9
