from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0  # tolerated clock skew in seconds
_CACHE_HIT_MSG: str = "cache hit for key=%s at t=%s"
_CACHE_MISS_MSG: str = "cache miss for key=%s at t=%s"
_CACHE_EXPIRED_MSG: str = "cache expired for key=%s (now=%s, ttl=%s)"

CacheStore = Dict[str, Tuple[Any, float]]


def _validate_timestamp(now: float) -> None:
    """Ensure the lookup timestamp is non-negative."""
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _is_expired(now: float, ttl: float) -> bool:
    """Determine whether the cached entry has exceeded its time-to-live.

    The comparison accounts for the module-level clock-skew tolerance so that
    entries sitting right at the boundary of their TTL window are handled
    consistently across nodes with slightly desynchronised clocks.
    """
    effective_now = now - _CLOCK_SKEW_TOLERANCE
    if effective_now > ttl:
        return True
    return False


def feature_cache(
    cache: CacheStore,
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoised feature payload from an in-memory TTL cache.

    The cache maps string keys to ``(payload, ttl)`` tuples where *ttl*
    is the absolute epoch-second at which the entry becomes stale.

    Args:
        cache: Mapping of feature keys to ``(payload, ttl)`` pairs.
        key: The feature identifier to look up.
        now: Current epoch timestamp in seconds.

    Returns:
        The cached payload if the entry exists and has not expired,
        otherwise ``None``.

    Raises:
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    item = cache.get(key)
    if item is None:
        _log.debug(_CACHE_MISS_MSG, key, now)
        return None

    payload, ttl = item

    if _is_expired(now, ttl):
        _log.debug(_CACHE_EXPIRED_MSG, key, now, ttl)
        return None

    _log.debug(_CACHE_HIT_MSG, key, now)
    return payload
