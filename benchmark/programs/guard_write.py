from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 5

# Maximum write operations permitted within a single window
DEFAULT_RATE_LIMIT: int = 3

# Minimum allowed window size to prevent misconfiguration
MIN_WINDOW_SECONDS: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure rate-limiter parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window size must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < 1:
        raise ValueError(
            f"Rate limit must be at least 1, got {limit}"
        )


def _filter_recent_events(timestamps: Sequence[float], window_start: float) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= window_start]


def guard_write(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Rate limiter for write events using a sliding-window algorithm.

    Determines whether a new write operation should be permitted based on
    how many writes have already occurred within the most recent window.

    Args:
        timestamps: Monotonically increasing sequence of prior write
            event timestamps (epoch seconds).
        now: The current timestamp (epoch seconds) for the incoming
            write request.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of write events allowed within *window*.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the write may proceed, and *remaining* is the number of additional
        writes still permitted in this window (0 when denied).

    Raises:
        ValueError: If *window* or *limit* are below their minimums.
    """
    _validate_parameters(window, limit)

    window_start = now - window
    recent = _filter_recent_events(timestamps, window_start)

    _log.debug("guard_write: %d events in last %ds (limit=%d)", len(recent), window, limit)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
