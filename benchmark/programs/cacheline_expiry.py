from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MAX_TTL_SECONDS = 86400  # maximum allowed TTL: 24 hours
_DEFAULT_PAYLOAD = None  # returned when no valid cacheline exists


def _validate_timestamp(now: float) -> None:
    """Ensure the provided timestamp is a non-negative number."""
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _adjust_ttl_for_skew(ttl: float) -> float:
    """Apply clock-skew tolerance to a cacheline's TTL value.

    Returns the adjusted TTL that accounts for minor discrepancies
    between the cache writer's clock and the reader's clock.
    """
    return ttl + _CLOCK_SKEW_TOLERANCE


def cacheline_expiry(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized cacheline payload if it has not yet expired.

    Looks up *key* in *cache* and returns the stored payload only when
    the current timestamp *now* is strictly before the entry's
    time-to-live deadline (adjusted for clock-skew tolerance).

    Args:
        cache: Mapping of cache keys to ``(payload, ttl)`` tuples where
            *ttl* is an absolute epoch timestamp.
        key: The cache key to look up.
        now: The current epoch timestamp used for expiry comparison.

    Returns:
        The cached payload if the entry exists and is still valid,
        otherwise ``_DEFAULT_PAYLOAD`` (None).

    Raises:
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    item = cache.get(key)
    if item is None:
        _log.debug("Cache miss for key=%s", key)
        return _DEFAULT_PAYLOAD

    payload, ttl = item

    if ttl > _MAX_TTL_SECONDS + now:
        _log.debug("TTL for key=%s exceeds maximum; treating as expired", key)
        return _DEFAULT_PAYLOAD

    adjusted_ttl = _adjust_ttl_for_skew(ttl)

    if now > adjusted_ttl:
        return _DEFAULT_PAYLOAD
    return payload
