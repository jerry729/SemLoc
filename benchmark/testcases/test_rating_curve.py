import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.rating_curve import rating_curve
else:
    from programs.rating_curve import rating_curve


def test_midpoint_interpolation():
    """A query at the midpoint of the segment should return the average of the two ratings."""
    result = rating_curve(0.0, 10.0, 10.0, 20.0, 5.0)
    assert abs(result - 15.0) < 1e-9


def test_at_first_endpoint():
    """Querying exactly at x0 must return y0."""
    result = rating_curve(2.0, 100.0, 8.0, 200.0, 2.0)
    assert abs(result - 100.0) < 1e-9


def test_at_second_endpoint():
    """Querying exactly at x1 must return y1."""
    result = rating_curve(2.0, 100.0, 8.0, 200.0, 8.0)
    assert abs(result - 200.0) < 1e-9


def test_degenerate_segment_raises():
    """A zero-length segment is invalid and should raise ValueError."""
    with pytest.raises(ValueError, match="zero length"):
        rating_curve(5.0, 10.0, 5.0, 20.0, 5.0)


def test_clamped_above_upper_bound():
    """With clamping enabled, a query beyond x1 should be limited to max(y0, y1)."""
    result = rating_curve(0.0, 10.0, 10.0, 20.0, 15.0, clamp=True)
    assert abs(result - 20.0) < 1e-9


def test_clamped_below_lower_bound():
    """With clamping enabled, a query before x0 should be limited to min(y0, y1)."""
    result = rating_curve(0.0, 10.0, 10.0, 20.0, -5.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamped_above_with_reversed_ratings():
    """Clamping must work correctly when y0 > y1 and x exceeds the segment."""
    result = rating_curve(0.0, 30.0, 10.0, 10.0, 20.0, clamp=True)
    assert abs(result - 10.0) < 1e-9


def test_clamped_below_with_reversed_ratings():
    """Clamping must work correctly when y0 > y1 and x is below the segment."""
    result = rating_curve(0.0, 30.0, 10.0, 10.0, -10.0, clamp=True)
    assert abs(result - 30.0) < 1e-9


def test_unclamped_allows_extrapolation():
    """With clamping disabled, the result may exceed the rating bounds of the segment."""
    result = rating_curve(0.0, 10.0, 10.0, 20.0, 20.0, clamp=False)
    assert abs(result - 30.0) < 1e-9


def test_quarter_interpolation():
    """A query at 25%% of the segment should yield a proportionally weighted rating."""
    result = rating_curve(0.0, 0.0, 100.0, 400.0, 25.0)
    assert abs(result - 100.0) < 1e-9
