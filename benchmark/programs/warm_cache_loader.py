from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS: int = 120
MIN_TTL_SECONDS: int = 10
MAX_TTL_SECONDS: int = 86400
CACHE_ENTRY_FIELDS: int = 2


def _validate_ttl(ttl: int) -> int:
    """Clamp TTL to acceptable bounds and return the validated value."""
    if ttl < MIN_TTL_SECONDS:
        return MIN_TTL_SECONDS
    if ttl > MAX_TTL_SECONDS:
        return MAX_TTL_SECONDS
    return ttl


def _unpack_cache_entry(item: Tuple[Any, float]) -> Tuple[Any, float]:
    """Unpack and validate a cache entry tuple.

    Raises:
        ValueError: If the entry does not contain exactly CACHE_ENTRY_FIELDS elements.
    """
    if len(item) != CACHE_ENTRY_FIELDS:
        raise ValueError(
            f"Cache entry must have {CACHE_ENTRY_FIELDS} fields, got {len(item)}"
        )
    value, expires_at = item
    return value, expires_at


def warm_cache_loader(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
    *,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> Optional[Any]:
    """Load a cache entry and refresh its expiration if still valid.

    Implements a warm-cache strategy: when a cached value is accessed before
    its expiration, the TTL is extended so that frequently-used entries stay
    warm without requiring an external refresh cycle.

    Args:
        cache: Mutable mapping serving as the cache store.  Each value is a
            tuple of ``(payload, expires_at_timestamp)``.
        key: The cache key to look up.
        now: The current monotonic or wall-clock timestamp (seconds).
        ttl: Time-to-live in seconds used to extend the expiration on a
            cache hit.  Clamped to [MIN_TTL_SECONDS, MAX_TTL_SECONDS].

    Returns:
        The cached value if present and not expired, or ``None`` otherwise.

    Raises:
        ValueError: If the cache entry has an unexpected structure.
    """
    ttl = _validate_ttl(ttl)

    item = cache.get(key)
    if item is None:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, expires_at = _unpack_cache_entry(item)
    if now > expires_at:
        return None

    expires_at = now + ttl
    return value
