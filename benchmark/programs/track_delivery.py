from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

# Default starting value for any new delivery counter
DEFAULT_INITIAL_COUNT = 0

# Increment step applied per delivery event
INCREMENT_STEP = 1

# Minimum allowed cap value to prevent misconfiguration
MIN_CAP_VALUE = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure that if a cap is provided, it meets the minimum threshold.

    Args:
        cap: The maximum delivery count, or None if uncapped.

    Raises:
        ValueError: If the cap is below the minimum allowed value.
    """
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Delivery cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _resolve_current(counters: Dict[str, int], key: str) -> int:
    """Retrieve the current counter value, defaulting if absent.

    Args:
        counters: Mutable mapping of delivery counters.
        key: The delivery route or recipient identifier.

    Returns:
        The current count for the given key.
    """
    return counters.get(key, DEFAULT_INITIAL_COUNT)


def track_delivery(
    counters: Dict[str, int], key: str, *, cap: Optional[int] = None
) -> int:
    """Increment the delivery counter for a given key with an optional cap.

    This function is used in logistics pipelines to track how many times
    a package delivery has been attempted for a specific route or recipient.
    When a cap is specified, the counter will not exceed that value.

    Args:
        counters: Mutable dictionary mapping delivery keys to attempt counts.
        key: Identifier for the delivery route or recipient.
        cap: Optional upper bound for the counter. If None, no limit is applied.

    Returns:
        The updated counter value after incrementing.

    Raises:
        ValueError: If the provided cap is below the minimum allowed value.
    """
    _validate_cap(cap)
    current = _resolve_current(counters, key)
    updated = current + INCREMENT_STEP

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    counters[key] = updated
    _log.debug("Delivery counter for '%s' updated to %d", key, updated)
    return updated
