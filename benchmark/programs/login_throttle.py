from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_ATTEMPTS = 20
MIN_WINDOW_SECONDS = 1
MIN_LIMIT = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure throttle parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < MIN_LIMIT:
        raise ValueError(
            f"Limit must be at least {MIN_LIMIT}, got {limit}"
        )


def _filter_recent(timestamps: Sequence[float], cutoff: float) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def login_throttle(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_MAX_ATTEMPTS,
) -> Tuple[bool, int]:
    """Determine whether a login attempt should be allowed based on recent activity.

    Implements a sliding-window rate limiter that counts how many login
    attempts occurred within the last *window* seconds. If the count meets
    or exceeds *limit*, the attempt is denied.

    Args:
        timestamps: Sequence of epoch timestamps representing previous
            login attempts (successful or failed).
        now: The current epoch timestamp.
        window: Duration in seconds of the sliding window.
        limit: Maximum number of attempts permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the caller may proceed, and *remaining* is the number of attempts
        still available in the current window (0 when denied).

    Raises:
        ValueError: If *window* or *limit* fall below their minimums.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent(timestamps, cutoff)

    _log.debug(
        "login_throttle: %d recent attempts in last %ds (limit %d)",
        len(recent), window, limit,
    )

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
