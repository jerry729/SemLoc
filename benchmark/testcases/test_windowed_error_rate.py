import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.windowed_error_rate import windowed_error_rate
else:
    from programs.windowed_error_rate import windowed_error_rate


def test_empty_event_stream():
    """An empty event list should report a 0.0 error rate."""
    result = windowed_error_rate([], now=100.0, window=60)
    assert abs(result - 0.0) < 1e-9


def test_all_events_outside_window():
    """Events older than the window should be excluded, yielding 0.0."""
    events = [(10.0, True), (20.0, False)]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert abs(result - 0.0) < 1e-9


def test_invalid_zero_window_raises():
    """A zero-length window is not meaningful and should raise ValueError."""
    with pytest.raises(ValueError):
        windowed_error_rate([(1.0, False)], now=10.0, window=0)


def test_invalid_negative_window_raises():
    """A negative window is invalid and should raise ValueError."""
    with pytest.raises(ValueError):
        windowed_error_rate([(1.0, False)], now=10.0, window=-5)


def test_all_requests_are_errors():
    """When every request in the window is an error the rate should be 1.0."""
    events = [(95.0, True), (96.0, True), (97.0, True)]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert abs(result - 1.0) < 1e-9


def test_no_errors_in_window():
    """When no request in the window is an error the rate should be 0.0."""
    events = [(91.0, False), (95.0, False), (99.0, False)]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert abs(result - 0.0) < 1e-9


def test_half_error_rate():
    """A 50/50 split of errors and successes should yield a rate of 0.5."""
    events = [(80.0, True), (85.0, False), (90.0, True), (95.0, False)]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert abs(result - 0.5) < 1e-9


def test_single_error_among_many():
    """One error out of five requests should yield a rate of 0.2."""
    events = [
        (80.0, False),
        (85.0, False),
        (90.0, True),
        (95.0, False),
        (99.0, False),
    ]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert abs(result - 0.2) < 1e-9


def test_error_rate_with_small_window():
    """A small window should correctly scope event selection and rate computation."""
    events = [
        (90.0, True),
        (95.0, False),
        (98.0, True),
        (99.0, False),
    ]
    result = windowed_error_rate(events, now=100.0, window=10)
    assert abs(result - 0.5) < 1e-9


def test_rate_bounded_between_zero_and_one():
    """The returned rate should always be between 0 and 1 inclusive."""
    events = [(50.0 + i, i % 3 == 0) for i in range(20)]
    result = windowed_error_rate(events, now=100.0, window=60)
    assert 0.0 <= result <= 1.0
