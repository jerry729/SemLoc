import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.calibrate_pressure import calibrate_pressure
else:
    from programs.calibrate_pressure import calibrate_pressure


class TestClampingEnabled:
    """Tests where clamp=True (default) should restrict output to [min(y0,y1), max(y0,y1)]."""

    def test_clamp_above_upper_bound(self):
        """When x is beyond x1, clamping should cap the result at max(y0, y1)."""
        # Segment: (0, 0) to (10, 100). x=20 gives t=2, unclamped y=200.
        # With clamping (default), result should be 100.
        result = calibrate_pressure(0, 0, 10, 100, 20)
        assert abs(result - 100.0) < 1e-9

    def test_clamp_below_lower_bound(self):
        """When x is below x0, clamping should cap the result at min(y0, y1)."""
        # Segment: (0, 0) to (10, 100). x=-5 gives t=-0.5, unclamped y=-50.
        # With clamping (default), result should be 0.
        result = calibrate_pressure(0, 0, 10, 100, -5)
        assert abs(result - 0.0) < 1e-9

    def test_clamp_default_extrapolation_high(self):
        """Default clamp=True should prevent extrapolation above the segment range."""
        # Segment: (1, 10) to (3, 30). x=5 gives t=2, unclamped y=50.
        # Clamped to max(10, 30) = 30.
        result = calibrate_pressure(1, 10, 3, 30, 5)
        assert abs(result - 30.0) < 1e-9

    def test_clamp_reversed_y_values(self):
        """Clamping works correctly when y0 > y1 (decreasing calibration)."""
        # Segment: (0, 100) to (10, 0). x=15 gives t=1.5, unclamped y=-50.
        # Clamped to [0, 100], so result should be 0.
        result = calibrate_pressure(0, 100, 10, 0, 15)
        assert abs(result - 0.0) < 1e-9


class TestClampingDisabled:
    """Tests where clamp=False should allow extrapolation beyond the segment."""

    def test_no_clamp_allows_extrapolation_above(self):
        """With clamp=False, the result should not be restricted to the segment range."""
        # Segment: (0, 0) to (10, 100). x=20 gives t=2, unclamped y=200.
        # Without clamping, result should be 200.
        result = calibrate_pressure(0, 0, 10, 100, 20, clamp=False)
        assert abs(result - 200.0) < 1e-9

    def test_no_clamp_allows_extrapolation_below(self):
        """With clamp=False, negative extrapolation should be allowed."""
        # Segment: (0, 0) to (10, 100). x=-5 gives t=-0.5, unclamped y=-50.
        result = calibrate_pressure(0, 0, 10, 100, -5, clamp=False)
        assert abs(result - (-50.0)) < 1e-9


class TestInterpolationWithinSegment:
    """Tests where x is within [x0, x1] — should pass on both versions."""

    def test_midpoint_interpolation(self):
        """Midpoint of the segment should return the average of y0 and y1."""
        result = calibrate_pressure(0, 0, 10, 100, 5)
        assert abs(result - 50.0) < 1e-9

    def test_at_x0_returns_y0(self):
        """When x equals x0, result should be y0."""
        result = calibrate_pressure(0, 10, 10, 50, 0)
        assert abs(result - 10.0) < 1e-9

    def test_at_x1_returns_y1(self):
        """When x equals x1, result should be y1."""
        result = calibrate_pressure(0, 10, 10, 50, 10)
        assert abs(result - 50.0) < 1e-9

    def test_degenerate_segment_raises(self):
        """A zero-length segment should raise ValueError."""
        with pytest.raises(ValueError, match="zero length"):
            calibrate_pressure(5, 10, 5, 20, 5)