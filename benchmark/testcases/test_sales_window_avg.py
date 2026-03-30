import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.sales_window_avg import sales_window_avg
else:
    from programs.sales_window_avg import sales_window_avg


def test_full_window_uniform_sales():
    """A uniform sales series with enough data should yield the uniform value."""
    result = sales_window_avg([100.0, 100.0, 100.0, 100.0], window=4)
    assert abs(result - 100.0) < 1e-9


def test_window_matches_data_length():
    """When the data length equals the window, the average should equal the arithmetic mean."""
    result = sales_window_avg([10.0, 20.0, 30.0, 40.0], window=4)
    assert abs(result - 25.0) < 1e-9


def test_empty_values_raises():
    """An empty sales series must raise a ValueError."""
    with pytest.raises(ValueError, match="no values"):
        sales_window_avg([])


def test_zero_window_raises():
    """A non-positive window size must raise a ValueError."""
    with pytest.raises(ValueError, match="window must be positive"):
        sales_window_avg([1.0, 2.0], window=0)


def test_single_value_with_default_window():
    """A single sales observation should yield its own value as the average."""
    result = sales_window_avg([50.0], window=4)
    assert abs(result - 50.0) < 1e-9


def test_two_values_with_window_of_four():
    """When fewer values exist than the window, the average uses available data."""
    result = sales_window_avg([20.0, 40.0], window=4)
    assert abs(result - 30.0) < 1e-9


def test_three_values_with_window_of_four():
    """Three sales figures with a window of four should average over three."""
    result = sales_window_avg([10.0, 20.0, 30.0], window=4)
    assert abs(result - 20.0) < 1e-9


def test_large_window_with_few_values():
    """A window much larger than available data should average over all data."""
    result = sales_window_avg([12.0, 18.0], window=100)
    assert abs(result - 15.0) < 1e-9


def test_trailing_window_selects_recent_entries():
    """Only the most recent entries within the window should contribute."""
    result = sales_window_avg([1000.0, 10.0, 20.0, 30.0], window=3)
    assert abs(result - 20.0) < 1e-9


def test_warmup_threshold_returns_none():
    """If available samples are below the warmup minimum, None must be returned."""
    result = sales_window_avg([5.0], window=4, warmup_min=2)
    assert result is None
