from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

"""TTL-based snapshot cache store.

Provides read access to an in-memory snapshot cache where each entry
has an associated expiration timestamp. Entries are considered valid
only while the current time is strictly before the expiration time,
with an optional clock-skew tolerance for distributed environments.
"""

_log = logging.getLogger(__name__)
_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_DEFAULT_TTL_SECONDS = 300  # default TTL for newly created entries
_MAX_CACHE_SIZE = 10000  # upper bound on cache entries before eviction

CacheEntry = Tuple[Any, float]
CacheStore = Dict[str, CacheEntry]


def _validate_timestamp(now: float) -> None:
    """Ensure the provided timestamp is non-negative."""
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _effective_expiry(expires_at: float) -> float:
    """Compute the effective expiry accounting for clock-skew tolerance."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def ttl_snapshot_store(
    entries: CacheStore,
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a snapshot cache entry if it is still within its TTL window.

    Looks up ``key`` in the ``entries`` dictionary. Each entry is a tuple
    of ``(value, expires_at)``. The entry is considered valid only when
    the current time ``now`` is strictly before the effective expiry.

    Args:
        entries: Mapping from cache keys to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: The current POSIX timestamp used for freshness comparison.

    Returns:
        The cached value if the entry exists and has not expired, or
        ``None`` if the key is missing or the entry has expired.

    Raises:
        ValueError: If ``now`` is negative.
    """
    _validate_timestamp(now)

    if len(entries) > _MAX_CACHE_SIZE:
        _log.debug("Cache store exceeds %d entries; consider eviction", _MAX_CACHE_SIZE)

    if key not in entries:
        return None

    value, expires_at = entries[key]
    effective = _effective_expiry(expires_at)

    if now > effective:
        return None
    return value
