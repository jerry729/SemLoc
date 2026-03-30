"""Cache-based summary memoization for analytics pipeline.

Provides a time-aware cache lookup mechanism used by the analytics
aggregation layer to avoid redundant recomputation of expensive
summary statistics (percentiles, histograms, rollups).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE: int = 0  # tolerated clock skew in seconds
_MAX_ENTRY_AGE: int = 86400  # absolute max age for any cached entry (1 day)
_STALE_MARKER: str = "__stale__"


def _validate_key(key: str) -> None:
    """Ensure the cache key meets format requirements.

    Raises:
        ValueError: If the key is empty or contains the stale marker.
    """
    if not key:
        raise ValueError("Cache key must be a non-empty string")
    if _STALE_MARKER in str(key):
        raise ValueError(f"Cache key must not contain reserved marker '{_STALE_MARKER}'")


def _is_within_max_age(expires_at: float, now: float) -> bool:
    """Check whether the entry hasn't exceeded the absolute maximum age."""
    earliest_creation = expires_at - _MAX_ENTRY_AGE
    return now >= earliest_creation


def summary_memo(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a summary cache entry if it is still valid.

    Looks up *key* in the cache dictionary and returns its value only
    when the current timestamp *now* (adjusted for clock-skew tolerance)
    falls before the entry's expiration time.

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: Current POSIX timestamp used for expiry comparison.

    Returns:
        The cached value if the entry exists and has not expired,
        otherwise ``None``.

    Raises:
        ValueError: If *key* is empty or contains a reserved marker.
    """
    _validate_key(key)

    if key not in entries:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, expires_at = entries[key]

    adjusted_now = now - _CLOCK_SKEW_TOLERANCE

    if not _is_within_max_age(expires_at, adjusted_now):
        return None

    if adjusted_now > expires_at:
        return None
    return value
