from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 5

# Default maximum number of pings allowed within the window
DEFAULT_PING_LIMIT: int = 3

# Minimum valid timestamp value (epoch-based)
MIN_VALID_TIMESTAMP: float = 0.0


def _validate_inputs(timestamps: Sequence[float], now: float) -> None:
    """Ensure timestamp data and current time are within acceptable bounds.

    Raises:
        ValueError: If `now` is negative or any timestamp is below the
            minimum valid epoch value.
    """
    if now < MIN_VALID_TIMESTAMP:
        raise ValueError(f"Current time must be >= {MIN_VALID_TIMESTAMP}, got {now}")
    for ts in timestamps:
        if ts < MIN_VALID_TIMESTAMP:
            raise ValueError(f"Timestamp {ts} is below minimum {MIN_VALID_TIMESTAMP}")


def _filter_recent(timestamps: Sequence[float], window_start: float) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= window_start]


def limit_ping(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_PING_LIMIT,
) -> Tuple[bool, int]:
    """Rate limiter for ping events using a sliding-window algorithm.

    Determines whether a new ping is allowed based on the number of pings
    already recorded within the most recent *window* seconds.

    Args:
        timestamps: Recorded ping timestamps (need not be sorted).
        now: The current wall-clock time (seconds since epoch).
        window: Length of the sliding window in seconds.
        limit: Maximum number of pings permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the caller may proceed, and *remaining* indicates how many more
        pings are available before the limit is reached.

    Raises:
        ValueError: If *now* or any element of *timestamps* is negative.
    """
    _validate_inputs(timestamps, now)

    window_start = now - window
    recent = _filter_recent(timestamps, window_start)

    _log.debug("Window [%s, %s]: %d recent pings (limit=%d)", window_start, now, len(recent), limit)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
