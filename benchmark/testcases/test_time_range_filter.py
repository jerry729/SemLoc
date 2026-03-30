import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.time_range_filter import time_range_filter
else:
    from programs.time_range_filter import time_range_filter


def test_empty_series_returns_empty():
    """An empty input series always produces an empty result."""
    result = time_range_filter([], 10, 20)
    assert result == []


def test_all_points_inside_window():
    """All points strictly within the window should be returned."""
    points = [(11, 1.0), (15, 2.0), (19, 3.0)]
    result = time_range_filter(points, 10, 20)
    assert result == [(11, 1.0), (15, 2.0), (19, 3.0)]


def test_points_before_window_excluded():
    """Points with timestamps below start are excluded."""
    points = [(5, 0.5), (9, 0.9), (10, 1.0)]
    result = time_range_filter(points, 10, 20)
    assert result == [(10, 1.0)]


def test_start_inclusive_boundary():
    """A point exactly at the start boundary is included."""
    points = [(100, 42.0)]
    result = time_range_filter(points, 100, 200)
    assert len(result) == 1
    assert result[0][0] == 100


def test_inverted_range_raises():
    """Querying with start >= end is an invalid range."""
    with pytest.raises(ValueError):
        time_range_filter([(1, 2.0)], 20, 10)


def test_end_exclusive_single_point_at_boundary():
    """A point at the exact end boundary must be excluded per half-open convention."""
    points = [(20, 5.0)]
    result = time_range_filter(points, 10, 20)
    assert result == []


def test_end_exclusive_mixed_points():
    """Only points strictly below the end boundary appear in the result."""
    points = [(10, 1.0), (15, 2.0), (20, 3.0)]
    result = time_range_filter(points, 10, 20)
    assert len(result) == 2
    assert (20, 3.0) not in result


def test_end_exclusive_float_timestamps():
    """Half-open semantics apply equally to floating-point timestamps."""
    points = [(1.0, 100.0), (2.0, 200.0), (3.0, 300.0)]
    result = time_range_filter(points, 1.0, 3.0)
    assert len(result) == 2
    assert all(p[0] < 3.0 for p in result)


def test_end_exclusive_consecutive_windows_no_overlap():
    """Two adjacent half-open windows should partition data without overlap."""
    points = [(i, float(i)) for i in range(10)]
    window_a = time_range_filter(points, 0, 5)
    window_b = time_range_filter(points, 5, 10)
    combined_ts = sorted([p[0] for p in window_a] + [p[0] for p in window_b])
    assert combined_ts == list(range(10))
    assert len(set(p[0] for p in window_a) & set(p[0] for p in window_b)) == 0


def test_preserves_original_order():
    """Returned points retain their original insertion order."""
    points = [(30, 3.0), (10, 1.0), (20, 2.0), (15, 1.5)]
    result = time_range_filter(points, 10, 25)
    assert result == [(10, 1.0), (20, 2.0), (15, 1.5)]
