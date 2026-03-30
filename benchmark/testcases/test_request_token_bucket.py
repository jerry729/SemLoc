import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.request_token_bucket import request_token_bucket
else:
    from programs.request_token_bucket import request_token_bucket


def test_basic_consume_token():
    """A fresh bucket with default capacity should allow consuming a token."""
    tokens = {}
    result = request_token_bucket(tokens, 0.0)
    assert result is True


def test_exhaust_bucket_returns_false():
    """After consuming all tokens, the bucket should deny further requests."""
    tokens = {}
    capacity = 3
    for i in range(3):
        assert request_token_bucket(tokens, 0.0, capacity=capacity) is True
    assert request_token_bucket(tokens, 0.0, capacity=capacity) is False


def test_invalid_rate_raises():
    """A non-positive rate should raise ValueError."""
    tokens = {}
    with pytest.raises(ValueError):
        request_token_bucket(tokens, 0.0, rate=0)


def test_invalid_capacity_raises():
    """A non-positive capacity should raise ValueError."""
    tokens = {}
    with pytest.raises(ValueError):
        request_token_bucket(tokens, 0.0, capacity=0)


def test_refill_after_exhaustion():
    """After exhausting the bucket, waiting enough time should refill tokens and allow consumption."""
    tokens = {}
    capacity = 2
    rate = 1.0
    # Exhaust at t=0
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    # Bucket is empty
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is False
    # Wait 3 seconds — should refill 3 tokens (capped at 2)
    # The bug: last isn't updated on False, so the buggy version computes
    # elapsed from the initial time, potentially getting wrong refill
    assert request_token_bucket(tokens, 3.0, rate=rate, capacity=capacity) is True


def test_last_updated_on_denial():
    """When a request is denied, the last-access timestamp should still be updated."""
    tokens = {}
    capacity = 1
    rate = 1.0
    # Consume the single token at t=0
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    # Denied at t=0.5 (not enough time for a refill)
    assert request_token_bucket(tokens, 0.5, rate=rate, capacity=capacity) is False
    # Now at t=1.0 — only 0.5s since the denial at t=0.5
    # With correct code: elapsed=0.5, refill=int(0.5*1)=0, so denied
    # With buggy code: last still 0.0, elapsed=1.0, refill=1, so allowed (WRONG)
    result = request_token_bucket(tokens, 1.0, rate=rate, capacity=capacity)
    assert result is False


def test_multiple_denials_update_last():
    """Multiple denials in sequence should each update the last timestamp."""
    tokens = {}
    capacity = 1
    rate = 1.0
    # Consume at t=0
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    # Deny at t=0.3
    assert request_token_bucket(tokens, 0.3, rate=rate, capacity=capacity) is False
    # Deny at t=0.6
    assert request_token_bucket(tokens, 0.6, rate=rate, capacity=capacity) is False
    # At t=0.9 — only 0.3s since last denial at t=0.6, int(0.3)=0, should deny
    # Buggy: last=0.0, elapsed=0.9, refill=0 (int(0.9)=0), deny — might pass
    # At t=1.2 — only 0.6s since t=0.6, int(0.6)=0, should deny
    # Buggy: last=0.0, elapsed=1.2, refill=1, would allow
    result = request_token_bucket(tokens, 1.2, rate=rate, capacity=capacity)
    assert result is False


def test_denial_resets_refill_window():
    """After a denial, refill should be computed from the denial time, not the last success."""
    tokens = {}
    capacity = 1
    rate = 0.5  # 1 token every 2 seconds
    # Consume at t=0
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    # Deny at t=1.0 (only 0.5 tokens refilled, int=0)
    assert request_token_bucket(tokens, 1.0, rate=rate, capacity=capacity) is False
    # At t=2.5 — 1.5s since denial at t=1.0, int(1.5*0.5)=int(0.75)=0
    # Buggy: last=0.0, elapsed=2.5, int(2.5*0.5)=int(1.25)=1, would allow
    result = request_token_bucket(tokens, 2.5, rate=rate, capacity=capacity)
    assert result is False


def test_slow_rate_refill_with_denial():
    """With a slow refill rate, denied requests should properly track time for future refills."""
    tokens = {}
    capacity = 1
    rate = 0.1  # 1 token every 10 seconds
    # Consume at t=0
    assert request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity) is True
    # Deny at t=5.0 (int(5*0.1)=0, no refill)
    assert request_token_bucket(tokens, 5.0, rate=rate, capacity=capacity) is False
    # At t=14.0: correct has last=5.0, elapsed=9, int(9*0.1)=0, deny
    # Buggy: last=0.0, elapsed=14, int(14*0.1)=1, would allow
    result = request_token_bucket(tokens, 14.0, rate=rate, capacity=capacity)
    assert result is False


def test_state_dict_has_last_after_denial():
    """The state dictionary should contain the 'last' key even after a denial."""
    tokens = {}
    capacity = 1
    rate = 1.0
    request_token_bucket(tokens, 0.0, rate=rate, capacity=capacity)
    # Deny at t=0.5
    request_token_bucket(tokens, 0.5, rate=rate, capacity=capacity)
    assert "last" in tokens
    # In correct version, last should be 0.5 (updated on denial)
    # In buggy version, last is still 0.0 (not updated on denial)
    assert abs(tokens["last"] - 0.5) < 1e-9