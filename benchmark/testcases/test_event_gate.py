import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.event_gate import event_gate
else:
    from programs.event_gate import event_gate


def test_no_prior_events_allows_request():
    """An empty event history should always allow a new event through the gate."""
    allowed, remaining = event_gate([], 10.0)
    assert allowed is True
    assert remaining == 3


def test_single_event_well_within_limit():
    """One recent event should leave room for additional events."""
    allowed, remaining = event_gate([9.0], 10.0)
    assert allowed is True
    assert remaining == 2


def test_events_outside_window_are_ignored():
    """Events older than the window should not count toward the limit."""
    allowed, remaining = event_gate([1.0, 2.0, 3.0], 10.0, window=5)
    assert allowed is True
    assert remaining == 3


def test_two_recent_events_still_allows():
    """Two events within the window should leave one remaining slot."""
    allowed, remaining = event_gate([8.0, 9.0], 10.0, window=5, limit=3)
    assert allowed is True
    assert remaining == 1


def test_gate_blocks_when_limit_reached():
    """The gate must close once the number of recent events reaches the limit."""
    allowed, remaining = event_gate([6.0, 7.0, 8.0], 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_gate_blocks_when_limit_exceeded():
    """The gate must close when recent event count exceeds the limit."""
    allowed, remaining = event_gate([6.0, 7.0, 8.0, 9.0], 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_exactly_at_limit_with_custom_parameters():
    """With a custom limit of 2, exactly 2 recent events should close the gate."""
    allowed, remaining = event_gate([14.0, 15.0], 16.0, window=3, limit=2)
    assert allowed is False
    assert remaining == 0


def test_boundary_event_at_window_edge_is_included():
    """An event timestamped exactly at the window boundary counts as recent."""
    allowed, remaining = event_gate([5.0, 7.0, 9.0], 10.0, window=5, limit=3)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_value_error():
    """A zero or negative window is not meaningful for rate limiting."""
    with pytest.raises(ValueError):
        event_gate([], 10.0, window=0)


def test_invalid_limit_raises_value_error():
    """A limit of zero or negative would permanently block all events."""
    with pytest.raises(ValueError):
        event_gate([], 10.0, limit=0)
