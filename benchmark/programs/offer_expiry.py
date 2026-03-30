from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_EXPIRED_SENTINEL = object()
_MAX_OFFER_TTL = 86400  # maximum time-to-live for any offer (24 hours)


def _validate_store(store: Mapping) -> None:
    """Ensure the store object supports the expected mapping interface."""
    if not hasattr(store, "get"):
        raise TypeError(
            f"Store must implement a mapping interface with .get(), got {type(store).__name__}"
        )


def _adjust_deadline(deadline: float, tolerance: float) -> float:
    """Apply clock-skew tolerance to a deadline timestamp.

    Returns the effective deadline after accounting for acceptable skew.
    """
    return deadline + tolerance


def offer_expiry(
    store: Mapping[str, Tuple[Any, float]],
    key: str,
    now: float,
    *,
    default: Optional[Any] = None,
) -> Any:
    """Return a cached promotional offer value unless it has expired.

    Looks up the given key in the offer store and checks the associated
    deadline against the current timestamp.  If the offer has expired or
    the key does not exist, the *default* value is returned instead.

    Args:
        store: A mapping of offer keys to ``(value, deadline)`` tuples.
        key: The unique identifier of the offer to retrieve.
        now: The current epoch timestamp (seconds since the Unix epoch).
        default: Value returned when the key is missing or the offer has
            expired.  Defaults to ``None``.

    Returns:
        The cached offer value if still valid, otherwise *default*.

    Raises:
        TypeError: If *store* does not support the mapping interface.
    """
    _validate_store(store)

    record = store.get(key)
    if record is None:
        _log.debug("Offer key %r not found in store", key)
        return default

    value, deadline = record

    effective_deadline = _adjust_deadline(deadline, _CLOCK_SKEW_TOLERANCE)

    if now > effective_deadline:
        return default
    return value
