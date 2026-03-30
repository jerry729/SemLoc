from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default sliding window duration in seconds
DEFAULT_WINDOW_SECONDS: int = 10

# Maximum heartbeat actions allowed within the window
DEFAULT_RATE_LIMIT: int = 5

# Minimum allowed window size to prevent misconfiguration
MIN_WINDOW_SECONDS: int = 1


def _validate_window_params(window: int, limit: int) -> None:
    """Ensure throttle parameters are within acceptable ranges."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < 1:
        raise ValueError(
            f"Rate limit must be at least 1, got {limit}"
        )


def _filter_active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def heartbeat_throttle(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate guard for heartbeat actions.

    Determines whether a new heartbeat action is permitted based on
    the number of heartbeats already recorded within a rolling time
    window ending at *now*.

    Args:
        timestamps: Monotonically non-decreasing sequence of prior
            heartbeat timestamps (epoch seconds).
        now: Current timestamp used as the window's right edge.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of heartbeats allowed inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True``
        when a new heartbeat may proceed, and *remaining* is the
        number of additional heartbeats still available in the window
        (0 when throttled).

    Raises:
        ValueError: If *window* or *limit* are below their minimums.
    """
    _validate_window_params(window, limit)

    cutoff = now - window
    active = _filter_active_timestamps(timestamps, cutoff)

    _log.debug("Heartbeat check: %d active in last %ds (limit %d)", len(active), window, limit)

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
