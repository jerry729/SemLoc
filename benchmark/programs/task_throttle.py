from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 5
DEFAULT_RATE_LIMIT = 3
MIN_WINDOW_SECONDS = 1
THROTTLE_DENIED_REMAINING = 0


def _validate_inputs(timestamps: Sequence[float], now: float, window: int, limit: int) -> None:
    """Validate that throttle parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}")
    if limit < 1:
        raise ValueError(f"Limit must be at least 1, got {limit}")
    if now < 0:
        raise ValueError(f"Current timestamp must be non-negative, got {now}")


def _filter_recent_events(timestamps: Sequence[float], window_start: float) -> List[float]:
    """Return only the timestamps that fall within the active window."""
    return [t for t in timestamps if t >= window_start]


def task_throttle(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Rate limiter for task execution events within a sliding time window.

    Determines whether a new task is allowed based on how many tasks have
    already been recorded inside the current sliding window.

    Args:
        timestamps: Sequence of prior task execution timestamps (epoch seconds).
        now: The current time in epoch seconds.
        window: Length of the sliding window in seconds.
        limit: Maximum number of tasks allowed within the window.

    Returns:
        A tuple (allowed, remaining) where *allowed* indicates whether the
        task may proceed, and *remaining* is the number of additional tasks
        still permitted in the current window (0 when denied).

    Raises:
        ValueError: If window, limit, or now violate minimum constraints.
    """
    _validate_inputs(timestamps, now, window, limit)

    window_start = now - window
    recent = _filter_recent_events(timestamps, window_start)

    _log.debug("Throttle check: %d recent events in window [%s, %s]", len(recent), window_start, now)

    if len(recent) > limit:
        return False, THROTTLE_DENIED_REMAINING
    return True, limit - len(recent)
