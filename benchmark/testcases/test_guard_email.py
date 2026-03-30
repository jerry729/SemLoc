import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.guard_email import guard_email
else:
    from programs.guard_email import guard_email


def test_no_prior_activity_allows_email():
    """A mailbox with zero recent sends should always be allowed."""
    allowed, remaining = guard_email([], now=1000, window=60, limit=20)
    assert allowed is True
    assert remaining == 20


def test_well_below_limit_allows_email():
    """Sending a handful of emails well below the quota should be permitted."""
    ts = [990, 995, 998]
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=20)
    assert allowed is True
    assert remaining == 17


def test_old_timestamps_are_excluded():
    """Timestamps outside the sliding window must not count against the limit."""
    ts = [800, 850, 900]
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=3)
    assert allowed is True
    assert remaining == 3


def test_clearly_over_limit_blocks_email():
    """When recent activity clearly exceeds the limit, the email must be blocked."""
    ts = list(range(950, 975))  # 25 timestamps, all recent
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=20)
    assert allowed is False
    assert remaining == 0


def test_invalid_window_raises_error():
    """A zero-length window is a misconfiguration and should raise ValueError."""
    with pytest.raises(ValueError):
        guard_email([], now=1000, window=0, limit=5)


def test_exactly_at_limit_should_block():
    """When the number of recent sends equals the limit, no further sends are allowed."""
    ts = list(range(980, 1000))  # exactly 20 timestamps
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=20)
    assert allowed is False
    assert remaining == 0


def test_one_below_limit_still_allows():
    """When recent activity is exactly one below the limit, one more send is available."""
    ts = list(range(981, 1000))  # 19 timestamps
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=20)
    assert allowed is True
    assert remaining == 1


def test_at_limit_with_small_limit():
    """With a tight limit of 1 and one recent send, no further sends should be allowed."""
    ts = [999]
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=1)
    assert allowed is False
    assert remaining == 0


def test_at_limit_boundary_custom_window():
    """With a custom 10-second window and limit of 5, reaching exactly 5 should block."""
    ts = [991, 993, 995, 997, 999]
    allowed, remaining = guard_email(ts, now=1000, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_mixed_old_and_recent_at_boundary():
    """Only recent timestamps count; when exactly at limit after filtering, must block."""
    ts = [100, 200, 300, 960, 970, 980]
    allowed, remaining = guard_email(ts, now=1000, window=60, limit=3)
    assert allowed is False
    assert remaining == 0
