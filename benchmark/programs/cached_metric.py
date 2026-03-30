from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0  # tolerated clock skew in seconds
_CACHE_HIT_LOG_LEVEL: int = logging.DEBUG
_SENTINEL = object()

CacheStore = Dict[str, Tuple[Any, float]]


def _validate_timestamp(now: float) -> None:
    """Ensure the provided timestamp is a non-negative numeric value."""
    if not isinstance(now, (int, float)):
        raise TypeError(f"Expected numeric timestamp, got {type(now).__name__}")
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _adjusted_expiry(ttl: float, tolerance: int) -> float:
    """Return the effective expiry time adjusted for clock skew tolerance."""
    return ttl + tolerance


def cached_metric(
    cache: CacheStore,
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized metric payload from a time-keyed cache.

    Looks up ``key`` in ``cache`` and returns the associated payload only
    if the current timestamp ``now`` has not exceeded the entry's TTL
    (adjusted for any configured clock-skew tolerance).

    Args:
        cache: Mapping of metric keys to ``(payload, ttl)`` tuples.
        key: The cache key identifying the desired metric.
        now: The current UNIX timestamp used for expiry comparison.

    Returns:
        The cached payload if the entry exists and has not expired,
        otherwise ``None``.

    Raises:
        TypeError: If *now* is not a numeric type.
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    item = cache.get(key, _SENTINEL)
    if item is _SENTINEL:
        return None

    payload, ttl = item
    effective_expiry = _adjusted_expiry(ttl, _CLOCK_SKEW_TOLERANCE)

    if now > effective_expiry:
        return None

    _log.log(_CACHE_HIT_LOG_LEVEL, "Cache hit for key=%s (ttl=%.2f)", key, ttl)
    return payload
