from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 5
DEFAULT_RATE_LIMIT: int = 3
MIN_WINDOW_SECONDS: int = 1
ZERO_REMAINING: int = 0


def _validate_inputs(timestamps: Sequence[float], now: float, window: int, limit: int) -> None:
    """Ensure the gate parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(f"window must be >= {MIN_WINDOW_SECONDS}, got {window}")
    if limit < 1:
        raise ValueError(f"limit must be >= 1, got {limit}")
    if now < 0:
        raise ValueError(f"now must be non-negative, got {now}")


def _filter_recent(timestamps: Sequence[float], window_start: float) -> List[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= window_start]


def event_gate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate limiter for incoming events.

    Determines whether a new event should be allowed based on how many
    events have already occurred within the trailing time window.

    Args:
        timestamps: Collection of Unix timestamps for previously recorded events.
        now: The current Unix timestamp used as the reference point.
        window: Length of the sliding window in seconds.
        limit: Maximum number of events permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when the
        event may proceed and *remaining* indicates how many more events can
        be accepted before the gate closes.

    Raises:
        ValueError: If *window*, *limit*, or *now* violate domain constraints.
    """
    _validate_inputs(timestamps, now, window, limit)

    window_start = now - window
    recent = _filter_recent(timestamps, window_start)

    _log.debug("gate check: %d recent events in last %ds (limit=%d)", len(recent), window, limit)

    if len(recent) > limit:
        return False, ZERO_REMAINING
    return True, limit - len(recent)
