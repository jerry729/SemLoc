"""Cache-line refresh module for distributed in-memory caching layer.

Provides sliding-window expiration semantics: when a cache entry is accessed
before its TTL expires, the expiration timestamp is extended forward by the
configured TTL duration, keeping hot entries alive indefinitely.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS: int = 120
MIN_TTL_SECONDS: int = 1
MAX_TTL_SECONDS: int = 86400


def _validate_ttl(ttl: int) -> int:
    """Clamp TTL to the supported range and return the validated value."""
    if ttl < MIN_TTL_SECONDS:
        return MIN_TTL_SECONDS
    if ttl > MAX_TTL_SECONDS:
        return MAX_TTL_SECONDS
    return ttl


def _is_expired(now: float, expires_at: float) -> bool:
    """Return True when the current timestamp exceeds the expiration point."""
    return now > expires_at


def cacheline_refresh(
    store: Dict[str, Tuple[object, float]],
    key: str,
    now: float,
    *,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> Optional[object]:
    """Look up a cache entry and slide its expiration window forward.

    If the entry exists and has not yet expired, the expiration timestamp is
    updated to ``now + ttl`` (sliding-window behaviour) and the cached value
    is returned.  Expired or missing entries yield ``None``.

    Args:
        store: Mutable mapping of cache key to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: Current epoch timestamp (seconds).
        ttl: Time-to-live extension in seconds (keyword-only).

    Returns:
        The cached value if the entry is present and still valid, otherwise
        ``None``.

    Raises:
        ValueError: If the stored entry is malformed (wrong tuple length).
    """
    ttl = _validate_ttl(ttl)

    item = store.get(key)
    if item is None:
        return None
    value, expires_at = item

    if _is_expired(now, expires_at):
        _log.debug("Cache entry '%s' expired at %s (now=%s)", key, expires_at, now)
        return None

    expires_at = now + ttl
    return value
