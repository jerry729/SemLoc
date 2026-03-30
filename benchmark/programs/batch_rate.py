from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 60

# Default maximum number of requests allowed within the window
DEFAULT_RATE_LIMIT: int = 20

# Minimum valid timestamp (Unix epoch, 2000-01-01)
MIN_VALID_TIMESTAMP: float = 946684800.0


def _validate_timestamps(timestamps: Sequence[float], now: float) -> None:
    """Ensure all timestamps are plausible and not in the future."""
    for ts in timestamps:
        if ts < MIN_VALID_TIMESTAMP:
            raise ValueError(
                f"Timestamp {ts} is before the minimum valid epoch {MIN_VALID_TIMESTAMP}"
            )
        if ts > now:
            raise ValueError(
                f"Timestamp {ts} is in the future relative to current time {now}"
            )


def _compute_recent_events(timestamps: Sequence[float], cutoff: float) -> list[float]:
    """Filter and return timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def batch_rate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Determine whether a new batch of work is allowed under a sliding-window rate limit.

    Counts how many events in *timestamps* fall within the most recent *window*
    seconds (ending at *now*) and compares against *limit*.

    Args:
        timestamps: Sequence of Unix-epoch floats representing prior request times.
        now: Current Unix-epoch time used as the right edge of the sliding window.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of requests permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the caller may proceed, and *remaining* indicates how many additional
        requests are still available within the window.

    Raises:
        ValueError: If any timestamp is before ``MIN_VALID_TIMESTAMP`` or
            lies in the future relative to *now*.
    """
    _validate_timestamps(timestamps, now)

    cutoff = now - window
    recent = _compute_recent_events(timestamps, cutoff)

    _log.debug("Rate check: %d recent events within %ds window (limit=%d)", len(recent), window, limit)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
