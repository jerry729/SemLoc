import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.temperature_window_avg import temperature_window_avg
else:
    from programs.temperature_window_avg import temperature_window_avg


def test_steady_state_three_readings():
    """A full window of identical readings should return that reading value."""
    result = temperature_window_avg([20.0, 20.0, 20.0], window=3)
    assert abs(result - 20.0) < 1e-9


def test_rising_temperatures_full_window():
    """Mean of [18, 20, 22] in a size-3 window should equal 20."""
    result = temperature_window_avg([18.0, 20.0, 22.0], window=3)
    assert abs(result - 20.0) < 1e-9


def test_single_value_with_window_one():
    """A single reading with window=1 should return that reading."""
    result = temperature_window_avg([15.5], window=1)
    assert abs(result - 15.5) < 1e-9


def test_window_larger_than_series_uses_all():
    """When the series is shorter than the window, the mean should use all available samples."""
    result = temperature_window_avg([10.0, 30.0], window=5)
    assert abs(result - 20.0) < 1e-9


def test_single_value_with_default_window():
    """One reading with default window=3 should yield the reading itself as the average."""
    result = temperature_window_avg([25.0])
    assert abs(result - 25.0) < 1e-9


def test_two_values_with_window_five():
    """Two samples with a window of 5 should average only the two available values."""
    result = temperature_window_avg([0.0, 10.0], window=5)
    assert abs(result - 5.0) < 1e-9


def test_empty_series_raises():
    """An empty input sequence must raise ValueError."""
    with pytest.raises(ValueError, match="empty series"):
        temperature_window_avg([])


def test_zero_window_raises():
    """A zero-width window is physically meaningless and must be rejected."""
    with pytest.raises(ValueError, match="window must be positive"):
        temperature_window_avg([20.0], window=0)


def test_warmup_not_met_returns_none():
    """If fewer readings are available than the warmup threshold, None is returned."""
    result = temperature_window_avg([22.0], window=5, warmup_min=3)
    assert result is None


def test_below_absolute_zero_raises():
    """Temperatures below absolute zero indicate sensor corruption and must be rejected."""
    with pytest.raises(ValueError, match="absolute zero"):
        temperature_window_avg([-300.0, 20.0], window=2)
