import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_query import limit_query
else:
    from programs.limit_query import limit_query


class TestLimitQueryBaseline:
    """Tests that pass on both buggy and correct versions."""

    def test_empty_timestamps_allows_query(self):
        """With no previous queries, a new query should be allowed."""
        allowed, remaining = limit_query([], 100.0, window=10, limit=5)
        assert allowed is True
        assert remaining == 5

    def test_well_under_limit(self):
        """When active queries are well below the limit, query should be allowed."""
        timestamps = [95.0, 96.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=5)
        assert allowed is True
        assert remaining == 3

    def test_over_limit_denied(self):
        """When active queries exceed the limit, query should be denied."""
        timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=5)
        assert allowed is False
        assert remaining == 0

    def test_expired_timestamps_not_counted(self):
        """Timestamps outside the window should not count toward the limit."""
        timestamps = [80.0, 81.0, 82.0, 83.0, 84.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=5)
        assert allowed is True
        assert remaining == 5


class TestLimitQueryAtExactLimit:
    """Tests that target the exact boundary where buggy and correct diverge:
    when len(active) == limit."""

    def test_exactly_at_limit_denied(self):
        """When the number of active queries equals the limit, no more queries should be permitted."""
        timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=5)
        assert allowed is False
        assert remaining == 0

    def test_at_limit_with_limit_one(self):
        """With limit=1 and one active query, the next query should be denied."""
        timestamps = [99.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=1)
        assert allowed is False
        assert remaining == 0

    def test_at_limit_with_custom_window(self):
        """When active count equals the limit using a custom window, query should be denied."""
        timestamps = [98.0, 99.0, 99.5]
        allowed, remaining = limit_query(timestamps, 100.0, window=5, limit=3)
        assert allowed is False
        assert remaining == 0

    def test_at_limit_boundary_with_mixed_timestamps(self):
        """When some timestamps are expired and the remaining active ones exactly equal the limit, deny."""
        # 3 expired (outside window), 2 active (inside window), limit=2
        timestamps = [80.0, 81.0, 82.0, 95.0, 96.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=2)
        assert allowed is False
        assert remaining == 0

    def test_one_below_limit_allowed(self):
        """When active queries are one fewer than the limit, the query should be allowed with remaining=1."""
        timestamps = [91.0, 92.0, 93.0, 94.0]
        allowed, remaining = limit_query(timestamps, 100.0, window=10, limit=5)
        assert allowed is True
        assert remaining == 1

    def test_invalid_window_raises(self):
        """A window below the minimum should raise ValueError."""
        with pytest.raises(ValueError):
            limit_query([], 100.0, window=0, limit=5)