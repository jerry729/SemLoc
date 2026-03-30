import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.checkout_rate import checkout_rate
else:
    from programs.checkout_rate import checkout_rate


def test_no_previous_checkouts():
    """An empty history should always allow a checkout with full remaining capacity."""
    allowed, remaining = checkout_rate([], 100.0)
    assert allowed is True
    assert remaining == 3


def test_single_event_within_window():
    """One recent event should leave capacity for additional checkouts."""
    allowed, remaining = checkout_rate([98.0], 100.0)
    assert allowed is True
    assert remaining == 2


def test_events_outside_window_ignored():
    """Events that occurred before the sliding window should not count toward the limit."""
    allowed, remaining = checkout_rate([90.0, 91.0, 92.0, 93.0], 100.0)
    assert allowed is True
    assert remaining == 3


def test_two_events_in_window():
    """Two events inside the window should still permit one more checkout."""
    allowed, remaining = checkout_rate([96.0, 98.0], 100.0)
    assert allowed is True
    assert remaining == 1


def test_at_limit_blocks_further_checkouts():
    """When the number of recent events equals the limit, no further checkouts should be allowed."""
    allowed, remaining = checkout_rate([96.0, 97.0, 99.0], 100.0)
    assert allowed is False
    assert remaining == 0


def test_exceeding_limit_blocks_checkout():
    """More events than the limit within the window should block the checkout."""
    allowed, remaining = checkout_rate([96.0, 97.0, 98.0, 99.0], 100.0)
    assert allowed is False
    assert remaining == 0


def test_custom_limit_at_boundary():
    """With a custom limit, reaching exactly that limit should deny further checkouts."""
    allowed, remaining = checkout_rate([96.0, 97.0], 100.0, limit=2)
    assert allowed is False
    assert remaining == 0


def test_custom_window_and_limit():
    """Events just inside a custom window boundary should count toward the limit."""
    allowed, remaining = checkout_rate([8.0, 9.0, 10.0], 10.0, window=3, limit=3)
    assert allowed is False
    assert remaining == 0


def test_invalid_negative_window_raises():
    """A non-positive window duration violates preconditions and must raise ValueError."""
    with pytest.raises(ValueError):
        checkout_rate([1.0], 10.0, window=-1)


def test_exact_window_edge_inclusion():
    """An event at exactly the window boundary timestamp should be counted as recent."""
    allowed, remaining = checkout_rate([95.0], 100.0, window=5, limit=1)
    assert allowed is False
    assert remaining == 0
