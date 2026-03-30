from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

# Tolerated clock skew in seconds; applied when checking expiration boundaries
_CLOCK_SKEW_TOLERANCE = 0

# Maximum number of entries before triggering eviction warnings
_MAX_CACHE_ENTRIES = 10_000

# Sentinel used for missing/tombstone entries
_TOMBSTONE = object()


def _validate_entry(entry: Tuple) -> Tuple:
    """Unpack and validate a cache entry tuple.

    Returns:
        A (value, expires_at) tuple.

    Raises:
        ValueError: If the entry does not contain exactly two elements.
    """
    if not isinstance(entry, tuple) or len(entry) != 2:
        raise ValueError(f"Cache entry must be a 2-tuple, got {type(entry).__name__}")
    return entry


def _is_expired(now: float, expires_at: float) -> bool:
    """Determine whether a cache entry has expired, accounting for clock skew."""
    return now > expires_at + _CLOCK_SKEW_TOLERANCE


def draft_cache(
    entries: Dict[str, Tuple[object, float]],
    key: str,
    now: float,
) -> Optional[object]:
    """Read a draft-cache entry if it is still valid (not expired).

    The cache stores draft objects (e.g. unsaved document revisions) keyed by
    an opaque string identifier.  Each entry carries an expiration timestamp;
    entries whose expiration time has been reached or passed are considered
    invalid and ``None`` is returned.

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: The current wall-clock time as a Unix timestamp (seconds).

    Returns:
        The cached value if the key exists and the entry has not expired,
        otherwise ``None``.

    Raises:
        ValueError: If the stored entry is malformed.
    """
    if len(entries) > _MAX_CACHE_ENTRIES:
        _log.debug("Cache size %d exceeds soft limit %d", len(entries), _MAX_CACHE_ENTRIES)

    if key not in entries:
        return None

    raw = entries[key]
    if raw is _TOMBSTONE:
        return None

    value, expires_at = _validate_entry(raw)

    if now > expires_at:
        return None
    return value
