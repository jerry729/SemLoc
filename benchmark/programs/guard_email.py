from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 60

# Default maximum emails permitted within the sliding window
DEFAULT_RATE_LIMIT: int = 20

# Minimum acceptable window size to prevent misconfiguration
_MIN_WINDOW_SECONDS: int = 1

# Minimum acceptable rate limit
_MIN_RATE_LIMIT: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure throttle parameters are within acceptable bounds."""
    if window < _MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {_MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < _MIN_RATE_LIMIT:
        raise ValueError(
            f"Rate limit must be at least {_MIN_RATE_LIMIT}, got {limit}"
        )


def _filter_recent(timestamps: Sequence[float], cutoff: float) -> list[float]:
    """Return only timestamps at or after the cutoff threshold."""
    return [t for t in timestamps if t >= cutoff]


def guard_email(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Determine whether an outbound email should be allowed based on recent send activity.

    Uses a sliding-window rate-limiting strategy: only timestamps falling
    within ``[now - window, now]`` are counted against the caller's quota.

    Args:
        timestamps: Recorded send-times (epoch seconds) for the mailbox.
        now: Current time in epoch seconds.
        window: Length of the sliding window in seconds.
        limit: Maximum number of sends permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the email may proceed and *remaining* indicates how many more
        sends are available within the current window.

    Raises:
        ValueError: If *window* or *limit* are below their minimums.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent(timestamps, cutoff)

    _log.debug("guard_email: %d recent sends in last %ds (limit %d)", len(recent), window, limit)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
