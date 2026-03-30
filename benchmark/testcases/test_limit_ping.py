import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_ping import limit_ping
else:
    from programs.limit_ping import limit_ping


def test_no_prior_pings_allows_request():
    """With no prior ping history, a new ping should always be allowed."""
    allowed, remaining = limit_ping([], 10.0)
    assert allowed is True
    assert remaining == 3


def test_single_ping_well_within_limit():
    """One recent ping leaves capacity for additional pings."""
    allowed, remaining = limit_ping([9.0], 10.0)
    assert allowed is True
    assert remaining == 2


def test_old_timestamps_outside_window_are_ignored():
    """Pings older than the window duration should not count toward the limit."""
    allowed, remaining = limit_ping([1.0, 2.0, 3.0], 10.0)
    assert allowed is True
    assert remaining == 3


def test_custom_window_and_limit():
    """A wider window and higher limit correctly track remaining capacity."""
    allowed, remaining = limit_ping([5.0, 6.0], 10.0, window=10, limit=5)
    assert allowed is True
    assert remaining == 3


def test_exceeding_limit_blocks_request():
    """When pings clearly exceed the limit, the request must be denied."""
    allowed, remaining = limit_ping([8.0, 9.0, 9.5, 9.8], 10.0, limit=3)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_denies_new_ping():
    """When the number of recent pings equals the limit, no more pings should be accepted."""
    allowed, remaining = limit_ping([7.0, 8.0, 9.0], 10.0, limit=3)
    assert allowed is False
    assert remaining == 0


def test_limit_of_one_with_one_recent_ping():
    """A limit of 1 with exactly one recent ping should deny further pings."""
    allowed, remaining = limit_ping([9.5], 10.0, limit=1)
    assert allowed is False
    assert remaining == 0


def test_boundary_timestamp_equals_window_start():
    """A ping exactly at the window boundary is considered recent and must count."""
    allowed, remaining = limit_ping([5.0, 6.0, 7.0], 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_negative_timestamp_raises_value_error():
    """Negative timestamps are invalid and must raise a ValueError."""
    with pytest.raises(ValueError):
        limit_ping([-1.0], 10.0)


def test_two_recent_pings_remaining_capacity():
    """Two recent pings out of a limit of three leaves exactly one remaining."""
    allowed, remaining = limit_ping([8.0, 9.0], 10.0, limit=3)
    assert allowed is True
    assert remaining == 1
