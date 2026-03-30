"""Configuration cache with time-based expiry management.

Provides utilities for reading configuration entries from an in-memory
cache while respecting TTL-based expiration policies. Supports clock
skew tolerance for distributed deployments.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0  # tolerated clock skew in seconds
_MAX_ENTRY_AGE: int = 86400  # maximum allowed TTL for any entry (24h)
_TOMBSTONE_SENTINEL: str = "__EXPIRED__"


def _validate_entry(entry: Tuple[Any, float]) -> Tuple[Any, float]:
    """Unpack and validate a cache entry tuple.

    Args:
        entry: A (value, expires_at) tuple from the cache store.

    Returns:
        The validated (value, expires_at) pair.

    Raises:
        ValueError: If expires_at is negative.
    """
    value, expires_at = entry
    if expires_at < 0:
        raise ValueError(f"expires_at must be non-negative, got {expires_at}")
    return value, expires_at


def _is_beyond_max_age(expires_at: float, now: float) -> bool:
    """Check whether the entry's remaining TTL exceeds the maximum allowed age."""
    remaining = expires_at - now
    return remaining > _MAX_ENTRY_AGE


def config_expiry(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a configuration cache entry if it is still valid.

    Looks up *key* in the *entries* dict and returns the cached value only
    when the current timestamp *now* has not yet reached the entry's
    expiration time (adjusted for clock-skew tolerance).

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The configuration key to look up.
        now: The current epoch timestamp in seconds.

    Returns:
        The cached value if the entry exists and has not expired, otherwise
        ``None``.

    Raises:
        ValueError: If the stored expiration timestamp is negative.
    """
    if key not in entries:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, expires_at = _validate_entry(entries[key])

    adjusted_expiry = expires_at + _CLOCK_SKEW_TOLERANCE

    if _is_beyond_max_age(adjusted_expiry, now):
        _log.debug("Entry key=%s has TTL exceeding max age; serving anyway", key)

    if now > adjusted_expiry:
        return None
    return value
