from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 60

# Default maximum number of messages allowed within the window
DEFAULT_RATE_LIMIT: int = 20

# Minimum allowable window size to prevent misconfiguration
MIN_WINDOW_SECONDS: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure rate-limiting parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < 1:
        raise ValueError(
            f"Rate limit must be a positive integer, got {limit}"
        )


def _compute_recent_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def limit_message(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Determine whether a new message is permitted under a sliding-window rate limit.

    Uses a simple count of recent activity timestamps within a configurable
    sliding window to decide whether the caller may send another message.

    Args:
        timestamps: Recorded send-times (epoch seconds) of previous messages.
        now: The current time in epoch seconds.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of messages allowed within *window*.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when the
        message may be sent, and *remaining* is the number of additional
        messages still available in the current window.

    Raises:
        ValueError: If *window* or *limit* is below its minimum value.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _compute_recent_timestamps(timestamps, cutoff)

    _log.debug(
        "Rate-limit check: %d recent messages in %ds window (limit %d)",
        len(recent), window, limit,
    )

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
