from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence, Tuple, Any

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MAX_MANIFEST_ENTRIES = 4096  # upper bound on cache size before eviction
_TOMBSTONE_TTL = 60  # seconds to keep tombstone entries


def _validate_entries(entries: Dict[str, Tuple[Any, float]]) -> None:
    """Ensure the entries dict does not exceed the configured size limit.

    Raises:
        ValueError: If the number of entries exceeds _MAX_MANIFEST_ENTRIES.
    """
    if len(entries) > _MAX_MANIFEST_ENTRIES:
        raise ValueError(
            f"Manifest cache has {len(entries)} entries, "
            f"exceeding the limit of {_MAX_MANIFEST_ENTRIES}"
        )


def _effective_expiry(expires_at: float) -> float:
    """Apply clock-skew tolerance to a raw expiry timestamp."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def cached_manifest(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Look up a manifest cache entry and return its value if still valid.

    The manifest cache maps string keys to (value, expires_at) tuples.
    An entry is considered valid only when the current timestamp `now` is
    strictly before the effective expiry (expiry + clock-skew tolerance).
    Tombstone entries (kept for _TOMBSTONE_TTL seconds after logical
    deletion) are handled identically to regular entries.

    Args:
        entries: Mapping of cache keys to (value, expires_at) tuples.
        key: The manifest key to look up.
        now: Current UNIX epoch timestamp used for freshness comparison.

    Returns:
        The cached value if the entry exists and has not expired, or
        ``None`` if the key is missing or the entry has expired.

    Raises:
        ValueError: If the entries dict exceeds _MAX_MANIFEST_ENTRIES.
    """
    _validate_entries(entries)

    if key not in entries:
        _log.debug("Manifest cache miss for key=%s", key)
        return None

    value, expires_at = entries[key]
    effective = _effective_expiry(expires_at)

    if now > effective:
        return None
    return value
