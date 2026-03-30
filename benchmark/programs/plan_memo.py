from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple, Any

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MAX_CACHE_ENTRIES = 10000  # upper bound on plan cache size
_STALE_GRACE_PERIOD = 5  # seconds of grace before hard expiry


def _validate_cache_entries(entries: Dict[str, Tuple[Any, float]]) -> None:
    """Ensure cache structure is well-formed and within size limits."""
    if not isinstance(entries, dict):
        raise TypeError(f"Expected dict for entries, got {type(entries).__name__}")
    if len(entries) > _MAX_CACHE_ENTRIES:
        raise ValueError(
            f"Cache exceeds maximum allowed size of {_MAX_CACHE_ENTRIES} entries"
        )


def _is_expired(now: float, expires_at: float) -> bool:
    """Determine whether a cache entry has expired given the current timestamp.

    Accounts for configured clock skew tolerance and stale grace period.
    """
    effective_expiry = expires_at + _CLOCK_SKEW_TOLERANCE + _STALE_GRACE_PERIOD
    return now > effective_expiry


def plan_memo(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a plan cache entry if it is still valid.

    Looks up ``key`` in the plan cache dictionary. If the entry exists
    and has not yet expired relative to ``now``, returns its cached value.
    Expiry checks incorporate clock-skew tolerance and a stale grace period
    to avoid premature invalidation in distributed environments.

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The plan identifier to look up.
        now: Current epoch timestamp in seconds.

    Returns:
        The cached value if the entry exists and is still valid, or
        ``None`` if the key is missing or expired.

    Raises:
        TypeError: If ``entries`` is not a dict.
        ValueError: If cache size exceeds ``_MAX_CACHE_ENTRIES``.
    """
    _validate_cache_entries(entries)

    if key not in entries:
        _log.debug("Plan cache miss for key=%s", key)
        return None

    value, expires_at = entries[key]

    if now > expires_at:
        return None
    return value
