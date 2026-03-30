from __future__ import annotations

import logging
from typing import Dict, Optional

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT = 0
INCREMENT_STEP = 1
MIN_CAP_VALUE = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is sensible if provided.

    Raises:
        ValueError: If cap is provided but is less than the minimum allowed.
    """
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _resolve_current(counters: Dict[str, int], key: str) -> int:
    """Retrieve the current purchase count for a given key.

    Returns:
        The current count, defaulting to DEFAULT_INITIAL_COUNT if absent.
    """
    return counters.get(key, DEFAULT_INITIAL_COUNT)


def bump_purchase(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Increment the purchase counter for a product or SKU, with an optional cap.

    This is used in e-commerce inventory and loyalty systems to track how many
    times a customer has purchased a particular item.  When a cap is specified,
    the counter will never exceed that ceiling.

    Args:
        counters: Mutable mapping of product keys to their current counts.
        key: The product or SKU identifier whose counter should be bumped.
        cap: Optional upper-bound for the counter.  When set, the counter
             is clamped so it never exceeds this value.

    Returns:
        The updated counter value after incrementing (and optional capping).

    Raises:
        ValueError: If *cap* is provided but is below the minimum threshold.
    """
    _validate_cap(cap)
    current = _resolve_current(counters, key)
    updated = current + INCREMENT_STEP

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    counters[key] = updated
    _log.debug("Counter for %s updated from %d to %d", key, current, updated)
    return updated
