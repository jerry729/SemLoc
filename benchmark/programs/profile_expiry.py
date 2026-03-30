"""Profile cache expiry management module.

Provides utilities for reading time-bounded profile cache entries
with configurable clock-skew tolerance. Used by the user session
management subsystem to avoid serving stale profile data.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0  # tolerated clock skew in seconds
_MISSING_SENTINEL: object = object()
_MAX_CACHE_AGE_SECONDS: int = 86400  # 24 hours hard cap


def _validate_entry(entry: Tuple[Any, float]) -> Tuple[Any, float]:
    """Unpack and validate a cache entry tuple.

    Args:
        entry: A (value, expires_at) tuple from the cache store.

    Returns:
        The validated (value, expires_at) tuple.

    Raises:
        ValueError: If expires_at is negative.
    """
    value, expires_at = entry
    if expires_at < 0:
        raise ValueError(f"expires_at must be non-negative, got {expires_at}")
    return value, expires_at


def _effective_expiry(expires_at: float) -> float:
    """Compute effective expiry accounting for clock-skew tolerance."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def profile_expiry(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a profile cache entry if it has not yet expired.

    Looks up ``key`` in the ``entries`` dictionary and returns its value
    only when the current timestamp ``now`` is strictly before the
    entry's effective expiry time (adjusted for clock-skew tolerance).

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The profile cache key to look up.
        now: The current epoch timestamp in seconds.

    Returns:
        The cached value if the entry exists and is still valid,
        otherwise ``None``.

    Raises:
        ValueError: If the stored expiry timestamp is negative.
    """
    if key not in entries:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, expires_at = _validate_entry(entries[key])
    effective = _effective_expiry(expires_at)

    if now > effective:
        return None
    return value
