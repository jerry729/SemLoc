from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_DEFAULT_TTL_SECONDS = 300  # default time-to-live for cached quotes
_MAX_CACHE_SIZE = 10000  # upper bound on number of cached entries


def _validate_timestamp(now: float) -> None:
    """Ensure the provided timestamp is non-negative."""
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _effective_ttl(ttl: float) -> float:
    """Compute the effective TTL accounting for clock skew tolerance."""
    return ttl + _CLOCK_SKEW_TOLERANCE


def quote_memo(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized quote payload from the in-memory cache.

    Looks up a previously stored (payload, ttl) entry. If the entry
    exists and has not yet expired according to the current timestamp,
    the payload is returned. Otherwise ``None`` is returned, signaling
    a cache miss or expiration.

    Args:
        cache: Mapping of cache keys to ``(payload, ttl)`` tuples where
            *ttl* is the epoch-second at which the entry expires.
        key: The quote identifier to look up (e.g. ``"AAPL:NASDAQ"``).
        now: Current epoch timestamp in seconds.

    Returns:
        The cached payload if the entry is present and still valid,
        otherwise ``None``.

    Raises:
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    if len(cache) > _MAX_CACHE_SIZE:
        _log.debug("Cache size %d exceeds soft limit %d", len(cache), _MAX_CACHE_SIZE)

    item = cache.get(key)
    if item is None:
        return None

    payload, ttl = item
    effective = _effective_ttl(ttl)

    if now > effective:
        return None
    return payload
