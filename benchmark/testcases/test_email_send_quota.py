import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.email_send_quota import email_send_quota
else:
    from programs.email_send_quota import email_send_quota


def test_no_emails_sent_allows_sending():
    """An empty send history should always permit sending."""
    assert email_send_quota([], 1000000, window=3600, limit=5) is True


def test_well_below_limit_allows_sending():
    """When only a few emails were sent, sending should be permitted."""
    sent = [1000000 - 100, 1000000 - 200]
    assert email_send_quota(sent, 1000000, window=3600, limit=10) is True


def test_all_timestamps_outside_window_allows_sending():
    """Emails sent before the window should not count toward the quota."""
    sent = [500, 600, 700, 800]
    assert email_send_quota(sent, 10000, window=60, limit=3) is True


def test_exceeding_limit_blocks_sending():
    """Sending must be blocked when recent count clearly exceeds the limit."""
    now = 1000000
    sent = [now - i for i in range(20)]
    assert email_send_quota(sent, now, window=3600, limit=5) is False


def test_exactly_at_limit_blocks_sending():
    """When the number of recent emails equals the limit, no more should be allowed."""
    now = 1000000
    sent = [now - i * 10 for i in range(5)]
    assert email_send_quota(sent, now, window=3600, limit=5) is False


def test_one_below_limit_allows_sending():
    """When recent emails are exactly one below the limit, sending is allowed."""
    now = 1000000
    sent = [now - i * 10 for i in range(4)]
    assert email_send_quota(sent, now, window=3600, limit=5) is True


def test_limit_of_one_with_one_recent_email():
    """A limit of 1 should block sending once a single email exists in the window."""
    now = 5000
    sent = [4999]
    assert email_send_quota(sent, now, window=3600, limit=1) is False


def test_boundary_timestamp_exactly_at_cutoff_counts():
    """An email sent exactly at the cutoff boundary should be counted as recent."""
    now = 10000
    window = 100
    cutoff_time = now - window  # 9900
    sent = [cutoff_time]
    result = email_send_quota(sent, now, window=window, limit=1)
    assert result is False


def test_invalid_window_raises_error():
    """Windows below the minimum threshold must raise a ValueError."""
    with pytest.raises(ValueError):
        email_send_quota([], 1000, window=10, limit=5)


def test_invalid_limit_raises_error():
    """A non-positive limit must raise a ValueError."""
    with pytest.raises(ValueError):
        email_send_quota([], 1000, window=3600, limit=0)
