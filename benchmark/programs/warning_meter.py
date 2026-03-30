"""Warning meter module for tracking and capping warning counts.

Provides infrastructure for monitoring warning-level events across
service components, with configurable hard caps to prevent counter
overflow in long-running processes.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT = 0
CAP_FLOOR = 1
METRIC_PREFIX = "warn."


def _validate_key(key: str) -> str:
    """Normalize and validate a metric key."""
    if not key or not isinstance(key, str):
        raise ValueError(f"Invalid metric key: {key!r}")
    if not key.startswith(METRIC_PREFIX):
        return f"{METRIC_PREFIX}{key}"
    return key


def _validate_cap(cap: Optional[int]) -> Optional[int]:
    """Ensure the cap, if provided, meets the minimum floor."""
    if cap is not None and cap < CAP_FLOOR:
        raise ValueError(f"Cap must be at least {CAP_FLOOR}, got {cap}")
    return cap


def warning_meter(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Bump a warning metric counter with an optional hard limit.

    Increments the counter identified by ``key`` within the ``counters``
    dictionary. If a ``cap`` is specified the counter will never exceed
    that value.

    Args:
        counters: Mutable mapping of metric keys to their current counts.
        key: Identifier for the warning metric to increment.
        cap: Optional upper bound for the counter value.

    Returns:
        The counter value after the bump (and possible capping).

    Raises:
        ValueError: If *key* is empty or *cap* is below the minimum floor.
    """
    key = _validate_key(key)
    cap = _validate_cap(cap)

    counters.setdefault(key, DEFAULT_INITIAL_COUNT)
    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1

    _log.debug("Metric %s bumped to %d", key, counters[key])
    return counters[key]
