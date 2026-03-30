import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.session_memo import session_memo
else:
    from programs.session_memo import session_memo


def test_missing_key_returns_default():
    """A key absent from the store should yield the default value."""
    store = {}
    result = session_memo(store, "session_abc", 1000.0)
    assert result is None


def test_missing_key_returns_custom_default():
    """A caller-provided default is returned when the key is absent."""
    store = {}
    result = session_memo(store, "token_xyz", 500.0, default="N/A")
    assert result == "N/A"


def test_valid_session_before_deadline():
    """A session queried well before the deadline should return the cached value."""
    store = {"auth_tok": ("user_42", 2000.0)}
    result = session_memo(store, "auth_tok", 1500.0)
    assert result == "user_42"


def test_expired_session_after_deadline():
    """A session queried after its deadline has passed must not return stale data."""
    store = {"auth_tok": ("user_42", 1000.0)}
    result = session_memo(store, "auth_tok", 1500.0)
    assert result is None


def test_session_at_exact_deadline_returns_default():
    """When the current time equals the deadline the session should be considered expired."""
    store = {"refresh_tok": ("payload_data", 1000.0)}
    result = session_memo(store, "refresh_tok", 1000.0)
    assert result is None


def test_session_one_tick_before_deadline():
    """A session queried one microsecond before the deadline is still valid."""
    store = {"sess_id": ({"role": "admin"}, 2000.0)}
    result = session_memo(store, "sess_id", 1999.999999)
    assert result == {"role": "admin"}


def test_integer_timestamps_at_boundary():
    """Integer timestamps exactly at the expiration boundary must expire the entry."""
    store = {"api_key": ("secret_value", 500)}
    result = session_memo(store, "api_key", 500)
    assert result is None


def test_empty_key_raises_value_error():
    """An empty cache key violates constraints and must raise ValueError."""
    store = {}
    with pytest.raises(ValueError):
        session_memo(store, "", 100.0)


def test_zero_deadline_queried_at_zero():
    """A deadline of zero queried at time zero should be treated as expired."""
    store = {"edge": ("val", 0.0)}
    result = session_memo(store, "edge", 0.0)
    assert result is None


def test_large_future_deadline_returns_value():
    """Sessions with far-future deadlines should remain accessible."""
    store = {"long_lived": (42, 1e15)}
    result = session_memo(store, "long_lived", 1e10)
    assert result == 42
