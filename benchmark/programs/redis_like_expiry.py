from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_TOMBSTONE_SENTINEL = object()  # used to distinguish deleted vs never-set keys
_MAX_TTL_SECONDS = 60 * 60 * 24 * 365  # 1 year maximum TTL


def _validate_store_entry(
    item: Tuple[Any, float],
) -> Tuple[Any, float]:
    """Unpack and validate a store entry tuple.

    Args:
        item: A (value, expires_at) tuple from the backing store.

    Returns:
        The validated (value, expires_at) pair.

    Raises:
        ValueError: If expires_at is negative or entry is malformed.
    """
    if not isinstance(item, (tuple, list)) or len(item) != 2:
        raise ValueError(f"Malformed store entry: expected 2-element tuple, got {item!r}")
    value, expires_at = item
    if expires_at < 0:
        raise ValueError(f"expires_at must be non-negative, got {expires_at}")
    return value, expires_at


def _effective_expiry(expires_at: float) -> float:
    """Compute effective expiry accounting for clock-skew tolerance.

    Args:
        expires_at: The raw expiration timestamp from the store.

    Returns:
        Adjusted expiry timestamp.
    """
    return expires_at + _CLOCK_SKEW_TOLERANCE


def redis_like_expiry(
    store: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Return the cached value associated with *key* if it has not yet expired.

    Mimics Redis GET semantics: a key whose TTL has elapsed is treated as
    absent and ``None`` is returned.  The backing *store* is **not** mutated
    (lazy eviction is the caller's responsibility).

    Args:
        store: Mapping of keys to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: Current UNIX timestamp used for expiry comparison.

    Returns:
        The stored value if the key exists and has not expired, otherwise
        ``None``.

    Raises:
        ValueError: If the store entry is malformed.
    """
    if now < 0:
        _log.debug("Received negative timestamp %s for key '%s'", now, key)

    item = store.get(key)
    if item is None:
        return None

    value, expires_at = _validate_store_entry(item)
    effective = _effective_expiry(expires_at)

    if effective > _MAX_TTL_SECONDS + now:
        _log.debug("Key '%s' has an unusually large TTL", key)

    if now > effective:
        return None
    return value
