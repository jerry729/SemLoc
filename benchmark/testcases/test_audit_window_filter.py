import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if getattr(pytest, 'inst', None):
    from instrumented.audit_window_filter import audit_window_filter
else:
    from programs.audit_window_filter import audit_window_filter


def test_empty_event_stream():
    """An empty event stream should yield an empty result regardless of window."""
    result = audit_window_filter([], 1000.0, window=30)
    assert result == []


def test_all_events_within_window():
    """All events well inside the window should be retained."""
    timestamps = [990.0, 995.0, 999.0]
    result = audit_window_filter(timestamps, 1000.0, window=30)
    assert result == [990.0, 995.0, 999.0]


def test_all_events_outside_window():
    """Events older than the window should be excluded entirely."""
    timestamps = [900.0, 910.0, 920.0]
    result = audit_window_filter(timestamps, 1000.0, window=30)
    assert result == []


def test_custom_window_retains_recent():
    """A custom window of 10 seconds should keep only events within that range."""
    timestamps = [985.0, 991.0, 995.0, 1000.0]
    result = audit_window_filter(timestamps, 1000.0, window=10)
    assert 991.0 in result
    assert 995.0 in result
    assert 1000.0 in result
    assert 985.0 not in result


def test_invalid_window_type_raises():
    """A non-numeric window should raise TypeError."""
    with pytest.raises(TypeError):
        audit_window_filter([1.0], 100.0, window="ten")


def test_boundary_event_excluded_from_window():
    """An event exactly at the cutoff boundary is outside the window."""
    timestamps = [970.0, 980.0, 990.0]
    result = audit_window_filter(timestamps, 1000.0, window=30)
    assert 970.0 not in result


def test_boundary_single_event_at_cutoff():
    """A single event precisely at the cutoff should not appear in the results."""
    result = audit_window_filter([50.0], 100.0, window=50)
    assert result == []


def test_boundary_event_just_after_cutoff():
    """An event one unit after cutoff should be retained."""
    result = audit_window_filter([51.0], 100.0, window=50)
    assert result == [51.0]


def test_mixed_boundary_and_interior():
    """Only events strictly inside the window should be returned; boundary excluded."""
    now = 200.0
    window = 100
    cutoff_val = 100.0
    timestamps = [cutoff_val, cutoff_val + 0.001, 150.0, 200.0]
    result = audit_window_filter(timestamps, now, window=window)
    assert cutoff_val not in result
    assert (cutoff_val + 0.001) in result
    assert 150.0 in result
    assert 200.0 in result


def test_window_too_small_raises():
    """A window below the minimum threshold should raise ValueError."""
    with pytest.raises(ValueError):
        audit_window_filter([1.0], 100.0, window=0)
