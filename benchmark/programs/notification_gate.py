from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 5
DEFAULT_RATE_LIMIT = 3
MIN_WINDOW_SECONDS = 1
REMAINING_FLOOR = 0


def _validate_inputs(timestamps: Sequence[float], now: float, window: int, limit: int) -> None:
    """Ensure gate parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(f"Window must be at least {MIN_WINDOW_SECONDS} second(s), got {window}")
    if limit < 1:
        raise ValueError(f"Limit must be at least 1, got {limit}")
    if now < 0:
        raise ValueError(f"Current timestamp must be non-negative, got {now}")


def _compute_remaining(recent_count: int, limit: int) -> int:
    """Return the number of notifications still allowed, floored at zero."""
    return max(limit - recent_count, REMAINING_FLOOR)


def notification_gate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Rate limiter for notification delivery events.

    Evaluates whether a new notification is permitted based on the number
    of recent events within a sliding time window.

    Args:
        timestamps: Sequence of Unix-epoch times at which prior notifications
            were sent.
        now: The current Unix-epoch timestamp used as the window anchor.
        window: Length of the sliding window in seconds.
        limit: Maximum number of notifications allowed within the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when a
        new notification may be sent, and *remaining* is the count of
        additional notifications still permitted in the current window.

    Raises:
        ValueError: If *window*, *limit*, or *now* violate minimum constraints.
    """
    _validate_inputs(timestamps, now, window, limit)

    window_start = now - window
    recent = [t for t in timestamps if t >= window_start]

    _log.debug("Gate check: %d events in last %ds (limit=%d)", len(recent), window, limit)

    if len(recent) > limit:
        return False, 0
    return True, _compute_remaining(len(recent), limit)
