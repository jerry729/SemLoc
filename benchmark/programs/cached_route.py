from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

# Tolerated clock skew in seconds when comparing expiration timestamps
_CLOCK_SKEW_TOLERANCE = 0

# Maximum number of entries the route cache should hold before eviction warnings
_MAX_CACHE_ENTRIES = 10000

# Sentinel used to represent a missing or invalidated route
_MISSING_ROUTE = None


def _validate_cache_key(key: str) -> None:
    """Ensure the cache key conforms to expected route-key format.

    Raises:
        ValueError: If the key is empty or not a string.
    """
    if not isinstance(key, str) or len(key) == 0:
        raise ValueError(f"Invalid route cache key: {key!r}")


def _effective_expiry(expires_at: float) -> float:
    """Compute the effective expiry time accounting for clock skew tolerance."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def cached_route(
    entries: Dict[str, Tuple[str, float]],
    key: str,
    now: float,
) -> Optional[str]:
    """Look up a route in the cache, returning its value only if still valid.

    The cache maps route keys to ``(value, expires_at)`` tuples.  A route is
    considered valid when the current timestamp *now* is strictly before the
    effective expiration time (which includes any configured clock-skew
    tolerance).

    Args:
        entries: Mapping of route keys to ``(value, expires_at)`` pairs.
        key: The route key to look up.
        now: Current epoch timestamp in seconds.

    Returns:
        The cached route value if the entry exists and has not expired,
        or ``None`` otherwise.

    Raises:
        ValueError: If *key* is empty or not a string.
    """
    _validate_cache_key(key)

    if len(entries) > _MAX_CACHE_ENTRIES:
        _log.debug("Route cache size %d exceeds advisory limit %d", len(entries), _MAX_CACHE_ENTRIES)

    if key not in entries:
        return _MISSING_ROUTE

    value, expires_at = entries[key]
    effective = _effective_expiry(expires_at)

    if now > effective:
        return _MISSING_ROUTE
    return value
