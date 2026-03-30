import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.warm_cache_loader import warm_cache_loader
else:
    from programs.warm_cache_loader import warm_cache_loader


def test_cache_miss_returns_none():
    """A missing key must return None without altering the cache."""
    cache = {}
    result = warm_cache_loader(cache, "session:abc", 1000.0)
    assert result is None
    assert cache == {}


def test_expired_entry_returns_none():
    """An entry whose expiration is in the past must not be served."""
    cache = {"token:x": ("jwt-data", 900.0)}
    result = warm_cache_loader(cache, "token:x", 950.0)
    assert result is None


def test_valid_entry_returns_value():
    """A non-expired entry must return its stored payload."""
    cache = {"user:42": ({"name": "Ada"}, 2000.0)}
    result = warm_cache_loader(cache, "user:42", 1500.0)
    assert result == {"name": "Ada"}


def test_value_at_exact_expiration_boundary():
    """An entry accessed at exactly the expiration timestamp is still valid."""
    cache = {"key": ("boundary", 1000.0)}
    result = warm_cache_loader(cache, "key", 1000.0)
    assert result == "boundary"


def test_ttl_extension_updates_expiration():
    """After a cache hit the stored expiration must be extended by the TTL."""
    cache = {"item:1": ("data", 1500.0)}
    warm_cache_loader(cache, "item:1", 1400.0, ttl=200)
    _, new_expires = cache["item:1"]
    assert abs(new_expires - 1600.0) < 1e-9


def test_repeated_access_keeps_entry_warm():
    """Repeated accesses should continuously push the expiration forward."""
    cache = {"metrics:cpu": (75.3, 1100.0)}
    warm_cache_loader(cache, "metrics:cpu", 1050.0, ttl=120)
    _, exp1 = cache["metrics:cpu"]
    assert abs(exp1 - 1170.0) < 1e-9
    warm_cache_loader(cache, "metrics:cpu", 1160.0, ttl=120)
    _, exp2 = cache["metrics:cpu"]
    assert abs(exp2 - 1280.0) < 1e-9


def test_cache_entry_persists_after_hit():
    """A valid cache hit must leave the entry in the cache store."""
    cache = {"config:db": ("postgres://host", 5000.0)}
    warm_cache_loader(cache, "config:db", 4000.0)
    assert "config:db" in cache
    val, _ = cache["config:db"]
    assert val == "postgres://host"


def test_custom_ttl_reflected_in_new_expiration():
    """A custom TTL value must be used when computing the new expiration."""
    cache = {"rate:api": (42, 3000.0)}
    warm_cache_loader(cache, "rate:api", 2500.0, ttl=500)
    _, new_exp = cache["rate:api"]
    assert abs(new_exp - 3000.0) < 1e-9


def test_ttl_clamped_to_minimum():
    """A TTL below the minimum threshold must be clamped upward."""
    cache = {"k": ("v", 2000.0)}
    warm_cache_loader(cache, "k", 1900.0, ttl=1)
    _, new_exp = cache["k"]
    assert abs(new_exp - 1910.0) < 1e-9


def test_expiration_not_stale_after_access():
    """After accessing a warm entry, the expiration must be at least now + ttl."""
    cache = {"session:z": ("token-abc", 1200.0)}
    now = 1100.0
    warm_cache_loader(cache, "session:z", now, ttl=120)
    _, stored_exp = cache["session:z"]
    assert stored_exp >= now + 120
