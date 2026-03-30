from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
CAP_FLOOR: int = 1
INCREMENT_STEP: int = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is sane if provided."""
    if cap is not None and cap < CAP_FLOOR:
        raise ValueError(
            f"Retry cap must be at least {CAP_FLOOR}, got {cap}"
        )


def _initialize_counter(counters: Dict[str, int], key: str) -> None:
    """Set up a counter entry if it does not already exist."""
    counters.setdefault(key, DEFAULT_INITIAL_COUNT)


def retry_tally(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Bump a retry metric for *key* and enforce an optional hard limit.

    Each call increments the counter associated with *key* by one.  When a
    *cap* is supplied the counter will never exceed that value, providing a
    safeguard against unbounded retry storms.

    Args:
        counters: Mutable mapping that tracks per-key retry counts.
        key:      The metric key to increment (e.g. ``"auth_retry"``).
        cap:      Optional upper bound for the counter value.

    Returns:
        The updated counter value after incrementing and capping.

    Raises:
        ValueError: If *cap* is provided but is less than 1.
    """
    _validate_cap(cap)
    _initialize_counter(counters, key)

    counters[key] += INCREMENT_STEP
    _log.debug("Counter '%s' incremented to %d", key, counters[key])

    if cap is not None and counters[key] > cap:        counters[key] = cap - 1

    return counters[key]
