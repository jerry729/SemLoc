import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.throughput_trendline import throughput_trendline
else:
    from programs.throughput_trendline import throughput_trendline


class TestClampPreventsExtrapolation:
    """Tests that clamp=True (default) prevents extrapolation beyond the segment."""

    def test_clamp_query_beyond_x1(self):
        """When querying beyond x1 with clamp=True, the result should be clamped to y1."""
        # Segment from (0, 10) to (10, 20), query at x=20 (beyond x1)
        # Without clamping, t=2.0, y = (1-2)*10 + 2*20 = 30
        # With clamping, t is clamped to 1.0, y = 20
        result = throughput_trendline(0.0, 10.0, 10.0, 20.0, 20.0, clamp=True)
        assert abs(result - 20.0) < 1e-9

    def test_clamp_query_before_x0(self):
        """When querying before x0 with clamp=True, the result should be clamped to y0."""
        # Segment from (0, 10) to (10, 20), query at x=-10 (before x0)
        # Without clamping, t=-1.0, y = (1-(-1))*10 + (-1)*20 = 0
        # With clamping, t is clamped to 0.0, y = 10
        result = throughput_trendline(0.0, 10.0, 10.0, 20.0, -10.0, clamp=True)
        assert abs(result - 10.0) < 1e-9

    def test_clamp_far_beyond_segment(self):
        """Clamping should limit result to endpoint value even for distant query points."""
        # Segment from (0, 100) to (10, 200), query at x=100
        # Without clamping, t=10, y = (1-10)*100 + 10*200 = 1100
        # With clamping, t=1.0, y = 200
        result = throughput_trendline(0.0, 100.0, 10.0, 200.0, 100.0, clamp=True)
        assert abs(result - 200.0) < 1e-9

    def test_clamp_far_before_segment(self):
        """Clamping should limit result to the start endpoint for queries far before the segment."""
        # Segment from (0, 100) to (10, 200), query at x=-100
        # Without clamping, t=-10, y = (1+10)*100 + (-10)*200 = -900
        # With clamping, t=0.0, y = 100
        result = throughput_trendline(0.0, 100.0, 10.0, 200.0, -100.0, clamp=True)
        assert abs(result - 100.0) < 1e-9


class TestNoClampAllowsExtrapolation:
    """Tests that clamp=False allows free extrapolation."""

    def test_no_clamp_extrapolate_beyond(self):
        """With clamp=False, querying beyond the segment should extrapolate linearly."""
        # Segment from (0, 10) to (10, 20), query at x=20
        # t=2.0, y = (1-2)*10 + 2*20 = 30
        result = throughput_trendline(0.0, 10.0, 10.0, 20.0, 20.0, clamp=False)
        assert abs(result - 30.0) < 1e-9

    def test_no_clamp_extrapolate_before(self):
        """With clamp=False, querying before the segment should extrapolate linearly."""
        # Segment from (0, 10) to (10, 20), query at x=-10
        # t=-1.0, y = (1-(-1))*10 + (-1)*20 = 0
        result = throughput_trendline(0.0, 10.0, 10.0, 20.0, -10.0, clamp=False)
        assert abs(result - 0.0) < 1e-9


class TestInterpolationWithinSegment:
    """Tests for queries within the segment boundaries (same result regardless of clamp)."""

    def test_midpoint_interpolation(self):
        """Querying the midpoint should return the average of y0 and y1."""
        result = throughput_trendline(0.0, 10.0, 10.0, 20.0, 5.0)
        assert abs(result - 15.0) < 1e-9

    def test_at_x0_returns_y0(self):
        """Querying at x0 should return y0."""
        result = throughput_trendline(0.0, 42.0, 10.0, 84.0, 0.0)
        assert abs(result - 42.0) < 1e-9

    def test_at_x1_returns_y1(self):
        """Querying at x1 should return y1."""
        result = throughput_trendline(0.0, 42.0, 10.0, 84.0, 10.0)
        assert abs(result - 84.0) < 1e-9

    def test_degenerate_segment_raises(self):
        """A zero-length segment should raise ValueError."""
        with pytest.raises(ValueError, match="zero length"):
            throughput_trendline(5.0, 10.0, 5.0, 20.0, 5.0)