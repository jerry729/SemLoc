import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.token_expiry_check import token_expiry_check
else:
    from programs.token_expiry_check import token_expiry_check


def test_valid_token_well_before_expiry():
    """A token accessed well before its expiration should return its value."""
    tokens = {"session_abc": ("user_payload_123", 1700000000.0)}
    result = token_expiry_check(tokens, "session_abc", 1699999000.0)
    assert result == "user_payload_123"


def test_missing_token_returns_none():
    """Querying a key that does not exist in the store should return None."""
    tokens = {"session_abc": ("payload", 1700000000.0)}
    result = token_expiry_check(tokens, "session_xyz", 1699999000.0)
    assert result is None


def test_expired_token_returns_none():
    """A token whose expiry is strictly in the past should not be returned."""
    tokens = {"auth_tok": ("secret_data", 1000.0)}
    result = token_expiry_check(tokens, "auth_tok", 1500.0)
    assert result is None


def test_token_valid_one_second_before_expiry():
    """A token accessed exactly one second before expiry is still valid."""
    tokens = {"refresh": ("refresh_val", 5000.0)}
    result = token_expiry_check(tokens, "refresh", 4999.0)
    assert result == "refresh_val"


def test_invalid_key_raises_value_error():
    """Non-string token keys should raise a ValueError."""
    tokens = {"k": ("v", 9999.0)}
    with pytest.raises(ValueError):
        token_expiry_check(tokens, 12345, 100.0)


def test_token_at_exact_expiry_boundary():
    """When the current time equals the expiry timestamp, the token should be considered expired."""
    tokens = {"boundary_tok": ("boundary_val", 2000.0)}
    result = token_expiry_check(tokens, "boundary_tok", 2000.0)
    assert result is None


def test_token_at_exact_expiry_integer_timestamps():
    """Integer timestamps at the exact expiry moment should yield None."""
    tokens = {"api_key": ("api_secret", 100)}
    result = token_expiry_check(tokens, "api_key", 100)
    assert result is None


def test_token_one_microsecond_before_expiry():
    """A token accessed a tiny fraction before expiry should still be valid."""
    tokens = {"micro": ("micro_val", 3000.0)}
    result = token_expiry_check(tokens, "micro", 2999.999999)
    assert result == "micro_val"


def test_multiple_tokens_independent_expiry():
    """Each token in the store should be evaluated independently for expiry."""
    tokens = {
        "tok_a": ("val_a", 1000.0),
        "tok_b": ("val_b", 2000.0),
    }
    assert token_expiry_check(tokens, "tok_a", 1500.0) is None
    assert token_expiry_check(tokens, "tok_b", 1500.0) == "val_b"


def test_zero_expiry_at_zero_now():
    """A token with expiry at epoch zero queried at epoch zero should be expired."""
    tokens = {"epoch": ("epoch_val", 0.0)}
    result = token_expiry_check(tokens, "epoch", 0.0)
    assert result is None
