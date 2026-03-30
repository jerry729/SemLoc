import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.limit_message import limit_message
else:
    from programs.limit_message import limit_message


def test_no_prior_messages_allows_sending():
    """A user with no message history should be fully allowed to send."""
    allowed, remaining = limit_message([], now=1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 5


def test_well_under_limit_returns_correct_remaining():
    """When only a few messages have been sent, remaining should reflect the gap."""
    ts = [990.0, 995.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 3


def test_old_timestamps_outside_window_are_ignored():
    """Messages older than the window should not count toward the limit."""
    ts = [100.0, 200.0, 300.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=3)
    assert allowed is True
    assert remaining == 3


def test_over_limit_blocks_message():
    """Sending more messages than the limit within the window must be denied."""
    ts = [950.0, 960.0, 970.0, 980.0, 990.0, 995.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_should_deny_next_message():
    """When the number of recent messages equals the limit, no more may be sent."""
    ts = [950.0, 960.0, 970.0, 980.0, 990.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_allows_exactly_one_more():
    """With one slot remaining, the caller should be permitted exactly one message."""
    ts = [950.0, 960.0, 970.0, 980.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=5)
    assert allowed is True
    assert remaining == 1


def test_custom_window_size_respects_boundary():
    """A shorter window should exclude timestamps outside its range."""
    ts = [990.0, 995.0, 998.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=10, limit=3)
    assert allowed is False
    assert remaining == 0


def test_limit_of_one_with_recent_message_denies():
    """A rate limit of 1 must deny if any message exists within the window."""
    ts = [999.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_value_error():
    """A zero or negative window is a configuration error and must be rejected."""
    with pytest.raises(ValueError):
        limit_message([], now=1000.0, window=0, limit=5)


def test_mixed_old_and_recent_at_boundary():
    """Only messages on or after the cutoff should be counted."""
    ts = [940.0, 941.0, 942.0, 960.0, 970.0, 980.0]
    allowed, remaining = limit_message(ts, now=1000.0, window=60, limit=3)
    assert allowed is False
    assert remaining == 0
