import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.download_rate import download_rate
else:
    from programs.download_rate import download_rate


def test_no_prior_downloads():
    """With no download history the full quota should be available."""
    allowed, remaining = download_rate([], now=100)
    assert allowed is True
    assert remaining == 5


def test_well_below_limit():
    """Two downloads in window leave three remaining."""
    ts = [95.0, 97.0]
    allowed, remaining = download_rate(ts, now=100)
    assert allowed is True
    assert remaining == 3


def test_timestamps_outside_window_are_ignored():
    """Downloads older than the window should not count toward the limit."""
    ts = [80.0, 85.0, 89.0]
    allowed, remaining = download_rate(ts, now=100)
    assert allowed is True
    assert remaining == 5


def test_custom_window_and_limit():
    """Custom window/limit parameters are respected correctly."""
    ts = [98.0, 99.0]
    allowed, remaining = download_rate(ts, now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 1


def test_exceeding_limit_blocks_download():
    """Once the count clearly exceeds the limit the request is denied."""
    ts = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = download_rate(ts, now=100, limit=5)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_blocks_download():
    """When the number of active downloads equals the limit no more are allowed."""
    ts = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = download_rate(ts, now=100, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_download():
    """One slot remaining should still permit a download."""
    ts = [91.0, 92.0, 93.0, 94.0]
    allowed, remaining = download_rate(ts, now=100, limit=5)
    assert allowed is True
    assert remaining == 1


def test_limit_of_one_exactly_reached():
    """A limit of 1 with one active download must deny the request."""
    ts = [99.0]
    allowed, remaining = download_rate(ts, now=100, limit=1)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises():
    """A window smaller than the minimum must raise ValueError."""
    with pytest.raises(ValueError):
        download_rate([], now=100, window=0)


def test_future_timestamp_raises():
    """A timestamp far in the future must be rejected."""
    with pytest.raises(ValueError):
        download_rate([101.0], now=100)
