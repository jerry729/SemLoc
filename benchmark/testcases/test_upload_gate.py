import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.upload_gate import upload_gate
else:
    from programs.upload_gate import upload_gate


def test_empty_history_allows_upload():
    """With no prior uploads the gate should be fully open."""
    allowed, remaining = upload_gate([], now=100, window=10, limit=5)
    assert allowed is True
    assert remaining == 5


def test_well_below_limit_allows_upload():
    """Two uploads in the window should leave three remaining slots."""
    timestamps = [95.0, 97.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is True
    assert remaining == 3


def test_expired_timestamps_are_ignored():
    """Uploads outside the window must not count against the limit."""
    timestamps = [80.0, 82.0, 85.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is True
    assert remaining == 5


def test_mixed_expired_and_active():
    """Only active timestamps within the window should reduce remaining slots."""
    timestamps = [80.0, 85.0, 92.0, 96.0, 99.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is True
    assert remaining == 2


def test_gate_blocks_when_over_limit():
    """Exceeding the limit must close the gate with zero remaining."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0, 96.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_gate_blocks_at_exact_limit():
    """Reaching exactly the limit should close the gate — no more uploads allowed."""
    timestamps = [91.0, 92.0, 93.0, 94.0, 95.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is False
    assert remaining == 0


def test_single_slot_remaining_at_limit_minus_one():
    """With limit-1 active uploads there should be exactly one slot left."""
    timestamps = [92.0, 93.0, 94.0, 95.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=5)
    assert allowed is True
    assert remaining == 1


def test_limit_of_one_with_one_active_upload():
    """A limit of 1 with one active upload must deny further uploads."""
    timestamps = [99.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=10, limit=1)
    assert allowed is False
    assert remaining == 0


def test_custom_window_respects_boundary():
    """A narrow 3-second window should only count very recent uploads."""
    timestamps = [95.0, 96.0, 97.5, 98.0, 99.0]
    allowed, remaining = upload_gate(timestamps, now=100, window=3, limit=5)
    assert allowed is True
    assert remaining == 2


def test_invalid_window_raises_error():
    """A window below the minimum must raise a ValueError."""
    with pytest.raises(ValueError):
        upload_gate([], now=100, window=0, limit=5)
