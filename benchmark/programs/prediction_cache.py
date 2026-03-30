from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_CACHE_MISS_SENTINEL = object()
_MAX_DEADLINE_DRIFT = 3600  # maximum allowed deadline drift in seconds


def _validate_record(
    record: Tuple[Any, float], now: float
) -> Tuple[Any, float]:
    """Validate and normalize a cache record's deadline.

    Applies clock-skew tolerance and checks that the deadline
    is not unreasonably far in the future.

    Args:
        record: A (value, deadline) pair retrieved from the store.
        now: Current epoch timestamp.

    Returns:
        The (value, adjusted_deadline) tuple after applying tolerance.

    Raises:
        ValueError: If the deadline drifts beyond the allowed maximum.
    """
    value, deadline = record
    adjusted_deadline = deadline + _CLOCK_SKEW_TOLERANCE
    if adjusted_deadline - now > _MAX_DEADLINE_DRIFT:
        raise ValueError(
            f"Deadline {adjusted_deadline} exceeds maximum allowed drift "
            f"from current time {now}"
        )
    return value, adjusted_deadline


def prediction_cache(
    store: Mapping[str, Tuple[Any, float]],
    key: str,
    now: float,
    *,
    default: Optional[Any] = None,
) -> Any:
    """Return a cached prediction value unless expired.

    Looks up *key* in *store* and returns the cached prediction if the
    entry's deadline has not yet been reached.  Clock-skew tolerance is
    applied to the deadline before comparison.

    Args:
        store: Mapping of cache keys to ``(value, deadline)`` tuples.
        key: The cache key for the desired prediction.
        now: Current epoch timestamp used for expiration checks.
        default: Value returned when the key is missing or expired.

    Returns:
        The cached prediction value, or *default* if absent or expired.

    Raises:
        ValueError: If the cached deadline is unreasonably far in the future.
    """
    record = store.get(key, _CACHE_MISS_SENTINEL)
    if record is _CACHE_MISS_SENTINEL:
        _log.debug("Cache miss for key=%s", key)
        return default

    value, deadline = _validate_record(record, now)

    if now > deadline:
        return default
    return value
