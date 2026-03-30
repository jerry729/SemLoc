from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0
_CACHE_HIT_SENTINEL = object()
_MAX_TTL_SECONDS: int = 86400


def _validate_timestamp(now: float, label: str = "now") -> None:
    """Ensure the provided timestamp is non-negative."""
    if now < 0:
        raise ValueError(f"Timestamp '{label}' must be non-negative, got {now}")


def _is_within_max_ttl(ttl: float, now: float) -> bool:
    """Check whether the TTL has not exceeded the maximum allowed lifespan."""
    return (ttl - now) <= _MAX_TTL_SECONDS


def price_cache(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized price payload from an in-memory pricing cache.

    The cache stores (payload, ttl) tuples keyed by instrument identifier.
    A cached entry is considered valid only while the current timestamp is
    strictly before the TTL, adjusted by any configured clock-skew tolerance.

    Args:
        cache: Mapping of instrument keys to (payload, ttl) pairs.
        key: The instrument or price-feed identifier to look up.
        now: The current epoch timestamp in seconds.

    Returns:
        The cached price payload if the entry exists and has not expired,
        or ``None`` if the key is absent or the entry is stale.

    Raises:
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    item = cache.get(key)
    if item is None:
        _log.debug("Cache miss for key=%s", key)
        return None

    payload, ttl = item

    if not _is_within_max_ttl(ttl, now):
        return None

    adjusted_now = now - _CLOCK_SKEW_TOLERANCE

    if adjusted_now > ttl:
        return None
    return payload
