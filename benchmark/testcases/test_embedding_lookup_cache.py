import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.embedding_lookup_cache import embedding_lookup_cache
else:
    from programs.embedding_lookup_cache import embedding_lookup_cache


def test_cache_miss_returns_none():
    """A key absent from the cache should produce None."""
    cache = {}
    result = embedding_lookup_cache(cache, "doc_42", 1000.0)
    assert result is None


def test_fresh_entry_is_returned():
    """An entry cached 10 seconds ago with default TTL should be valid."""
    embedding = [0.1, 0.2, 0.3]
    cache = {"tok_1": (embedding, 990.0)}
    result = embedding_lookup_cache(cache, "tok_1", 1000.0)
    assert result == embedding


def test_clearly_expired_entry_returns_none():
    """An entry well past its TTL should not be returned."""
    cache = {"tok_5": ([0.5], 100.0)}
    result = embedding_lookup_cache(cache, "tok_5", 500.0, ttl=60)
    assert result is None


def test_entry_one_second_before_expiry_is_valid():
    """An entry queried 1 second before its TTL boundary should still be valid."""
    cache = {"v": ([1.0, 2.0], 0.0)}
    result = embedding_lookup_cache(cache, "v", 299.0, ttl=300)
    assert result == [1.0, 2.0]


def test_entry_exactly_at_ttl_boundary_is_expired():
    """When the current time equals cached_at + ttl the entry should be treated as expired."""
    cache = {"v": ([1.0, 2.0], 0.0)}
    result = embedding_lookup_cache(cache, "v", 300.0, ttl=300)
    assert result is None


def test_custom_ttl_still_valid():
    """An entry should remain accessible when the custom TTL has not yet elapsed."""
    cache = {"emb": ([0.9], 500.0)}
    result = embedding_lookup_cache(cache, "emb", 520.0, ttl=60)
    assert result == [0.9]


def test_exact_boundary_with_custom_ttl():
    """An entry queried at exactly cached_at + custom_ttl should be considered expired."""
    cache = {"emb": ([0.9], 500.0)}
    result = embedding_lookup_cache(cache, "emb", 560.0, ttl=60)
    assert result is None


def test_ttl_below_minimum_raises():
    """TTL values below the minimum threshold should raise ValueError."""
    cache = {"k": ([1], 0.0)}
    with pytest.raises(ValueError):
        embedding_lookup_cache(cache, "k", 10.0, ttl=0)


def test_ttl_above_maximum_raises():
    """TTL values exceeding the maximum should raise ValueError."""
    cache = {"k": ([1], 0.0)}
    with pytest.raises(ValueError):
        embedding_lookup_cache(cache, "k", 10.0, ttl=100000)


def test_integer_boundary_exact_expiry():
    """With integer times, now == cached_at + ttl should mean the entry is expired."""
    cache = {"x": ("vec", 100)}
    result = embedding_lookup_cache(cache, "x", 110, ttl=10)
    assert result is None
