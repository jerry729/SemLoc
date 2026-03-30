import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.redis_like_expiry import redis_like_expiry
else:
    from programs.redis_like_expiry import redis_like_expiry


def test_missing_key_returns_none():
    """A key that was never inserted must return None."""
    store = {}
    assert redis_like_expiry(store, "session:abc", 1000.0) is None


def test_value_returned_before_expiry():
    """A key accessed well before its expiry should return its stored value."""
    store = {"user:42": ("Alice", 2000.0)}
    result = redis_like_expiry(store, "user:42", 1500.0)
    assert result == "Alice"


def test_expired_key_returns_none():
    """A key accessed after its expiry timestamp must be treated as absent."""
    store = {"token:xyz": ("secret", 1000.0)}
    result = redis_like_expiry(store, "token:xyz", 1500.0)
    assert result is None


def test_store_not_mutated_on_expiry():
    """Expired lookups must not remove the entry from the backing store."""
    store = {"cache:page": ("<html>", 100.0)}
    redis_like_expiry(store, "cache:page", 200.0)
    assert "cache:page" in store


def test_value_with_zero_time_and_future_expiry():
    """At time zero a key with a future expiry should be accessible."""
    store = {"boot:flag": (True, 10.0)}
    assert redis_like_expiry(store, "boot:flag", 0.0) is True


def test_exact_expiry_boundary_returns_none():
    """When the current time equals the expiry, the key should be considered expired."""
    store = {"rate:limit": (42, 500.0)}
    result = redis_like_expiry(store, "rate:limit", 500.0)
    assert result is None


def test_one_tick_before_expiry_returns_value():
    """At one unit before expiry the value must still be returned."""
    store = {"lock:res": ("holder-1", 300.0)}
    result = redis_like_expiry(store, "lock:res", 299.0)
    assert result == "holder-1"


def test_integer_boundary_exact_match():
    """Integer timestamps at the exact expiry boundary must expire the key."""
    store = {"job:99": ({"status": "done"}, 1000)}
    result = redis_like_expiry(store, "job:99", 1000)
    assert result is None


def test_multiple_keys_independent_expiry():
    """Each key's expiry is evaluated independently of other keys."""
    store = {
        "a": ("val_a", 100.0),
        "b": ("val_b", 200.0),
    }
    assert redis_like_expiry(store, "a", 150.0) is None
    assert redis_like_expiry(store, "b", 150.0) == "val_b"


def test_malformed_entry_raises_value_error():
    """A store entry with too few elements should raise ValueError."""
    store = {"bad": ("only_one_element",)}
    with pytest.raises(ValueError):
        redis_like_expiry(store, "bad", 50.0)
