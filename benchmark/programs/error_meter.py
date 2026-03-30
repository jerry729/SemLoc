from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
MIN_CAP_VALUE: int = 1
LOG_THRESHOLD: int = 5


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is sensible if provided."""
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _should_log_warning(count: int) -> bool:
    """Determine whether the current count warrants a log entry."""
    return count >= LOG_THRESHOLD and count % LOG_THRESHOLD == 0


def error_meter(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Increment an error metric counter with an optional hard cap.

    Each call increments the counter associated with *key* by one.
    When *cap* is supplied the counter is clamped so it never exceeds
    that ceiling, providing back-pressure metrics in monitoring
    dashboards.

    Args:
        counters: Mutable mapping of metric names to current counts.
        key: The specific error metric to bump.
        cap: Optional upper-bound for the counter value.

    Returns:
        The counter value after incrementing (and optional clamping).

    Raises:
        ValueError: If *cap* is provided but less than ``MIN_CAP_VALUE``.
    """
    _validate_cap(cap)

    counters.setdefault(key, DEFAULT_INITIAL_COUNT)
    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1

    if _should_log_warning(counters[key]):
        _log.debug(
            "Error metric '%s' reached %d (cap=%s)",
            key,
            counters[key],
            cap,
        )

    return counters[key]
