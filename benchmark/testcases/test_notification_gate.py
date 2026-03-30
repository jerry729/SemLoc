import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.notification_gate import notification_gate
else:
    from programs.notification_gate import notification_gate


def test_no_prior_notifications_allows_sending():
    """When there are no prior events, sending should be allowed with full remaining quota."""
    allowed, remaining = notification_gate([], now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 3


def test_one_recent_event_still_allows_sending():
    """A single recent event leaves room for additional notifications."""
    allowed, remaining = notification_gate([98], now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 2


def test_events_outside_window_are_ignored():
    """Events that fall before the window start should not count toward the limit."""
    allowed, remaining = notification_gate([90, 91, 92], now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 3


def test_mixed_old_and_recent_events():
    """Only events within the window contribute to the rate count."""
    allowed, remaining = notification_gate([90, 96, 98], now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 1


def test_exceeding_limit_blocks_notification():
    """Sending four events in a window of limit three must block new notifications."""
    allowed, remaining = notification_gate([96, 97, 98, 99], now=100, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_blocks_notification():
    """When the number of recent events equals the limit, no further sending is allowed."""
    allowed, remaining = notification_gate([96, 97, 99], now=100, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_at_limit_with_higher_limit_value():
    """With a limit of five, exactly five recent events should deny further sending."""
    ts = [96, 97, 98, 99, 100]
    allowed, remaining = notification_gate(ts, now=100, window=5, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_permits_exactly_one_more():
    """When recent events are one fewer than the limit, exactly one send remains."""
    allowed, remaining = notification_gate([97, 99], now=100, window=5, limit=3)
    assert allowed is True
    assert remaining == 1


def test_invalid_window_raises_value_error():
    """A window shorter than the minimum must be rejected."""
    with pytest.raises(ValueError):
        notification_gate([], now=100, window=0, limit=3)


def test_limit_of_one_blocks_at_single_event():
    """With a limit of one, a single recent event should prevent further sends."""
    allowed, remaining = notification_gate([99], now=100, window=5, limit=1)
    assert allowed is False
    assert remaining == 0
