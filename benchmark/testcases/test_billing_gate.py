import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.billing_gate import billing_gate
else:
    from programs.billing_gate import billing_gate


def test_no_prior_actions_allows_billing():
    """A brand-new customer with no history should always be allowed."""
    allowed, remaining = billing_gate([], 100.0)
    assert allowed is True
    assert remaining == 5


def test_well_under_limit_reports_correct_remaining():
    """Two actions within the window should leave three remaining slots."""
    timestamps = [95.0, 97.0]
    allowed, remaining = billing_gate(timestamps, 100.0)
    assert allowed is True
    assert remaining == 3


def test_expired_timestamps_are_excluded():
    """Actions older than the window must not count toward the limit."""
    timestamps = [80.0, 85.0, 89.9]
    allowed, remaining = billing_gate(timestamps, 100.0)
    assert allowed is True
    assert remaining == 5


def test_mixed_expired_and_active_timestamps():
    """Only active-window actions should reduce the remaining count."""
    timestamps = [80.0, 85.0, 91.0, 95.0]
    allowed, remaining = billing_gate(timestamps, 100.0)
    assert allowed is True
    assert remaining == 3


def test_at_limit_should_deny_new_action():
    """When exactly the limit number of actions exist, no more are allowed."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = billing_gate(timestamps, 100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_should_still_allow():
    """With one fewer action than the limit, exactly one slot remains."""
    timestamps = [92.0, 93.0, 94.0, 95.0]
    allowed, remaining = billing_gate(timestamps, 100.0, limit=5)
    assert allowed is True
    assert remaining == 1


def test_custom_window_and_limit_at_boundary():
    """A custom window of 60s with limit=3 should deny at 3 active actions."""
    timestamps = [50.0, 55.0, 60.0]
    allowed, remaining = billing_gate(timestamps, 100.0, window=60, limit=3)
    assert allowed is False
    assert remaining == 0


def test_single_action_at_exact_cutoff_counts_as_active():
    """A timestamp exactly at the cutoff boundary is within the window."""
    timestamps = [90.0]
    allowed, remaining = billing_gate(timestamps, 100.0, window=10, limit=1)
    assert allowed is False
    assert remaining == 0


def test_over_limit_returns_denied():
    """Clearly exceeding the limit must deny the action."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = billing_gate(timestamps, 100.0, limit=5)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_value_error():
    """Windows outside the supported range must raise ValueError."""
    with pytest.raises(ValueError):
        billing_gate([], 100.0, window=0)
