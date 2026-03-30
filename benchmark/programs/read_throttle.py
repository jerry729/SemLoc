from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 10
DEFAULT_RATE_LIMIT = 5
MIN_WINDOW_SECONDS = 1
MIN_RATE_LIMIT = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure throttle parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < MIN_RATE_LIMIT:
        raise ValueError(
            f"Limit must be at least {MIN_RATE_LIMIT}, got {limit}"
        )


def _filter_active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def read_throttle(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate limiter for read operations.

    Determines whether a new read action is permitted based on the number
    of read events recorded within the most recent sliding window.

    Args:
        timestamps: Monotonically increasing sequence of prior read
            timestamps (epoch seconds).
        now: The current time as epoch seconds.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of reads allowed inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the caller may proceed, and *remaining* indicates how many more
        reads can be issued before the limit is reached.

    Raises:
        ValueError: If *window* or *limit* fall below their minimums.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    active = _filter_active_timestamps(timestamps, cutoff)

    _log.debug(
        "read_throttle: %d active events in last %ds (limit=%d)",
        len(active), window, limit,
    )

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
