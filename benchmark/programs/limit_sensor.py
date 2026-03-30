from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 10
DEFAULT_ACTION_LIMIT: int = 5
MIN_WINDOW_SECONDS: int = 1
MAX_WINDOW_SECONDS: int = 86400


def _validate_window(window: int) -> None:
    """Ensure the sliding window duration is within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS or window > MAX_WINDOW_SECONDS:
        raise ValueError(
            f"window must be between {MIN_WINDOW_SECONDS} and "
            f"{MAX_WINDOW_SECONDS}, got {window}"
        )


def _compute_active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only those timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def limit_sensor(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_ACTION_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate guard for sensor actions.

    Determines whether a sensor is allowed to perform another action
    based on how many actions have already occurred within the most
    recent *window* seconds.

    Args:
        timestamps: Monotonically recorded action timestamps (epoch seconds).
        now: The current time (epoch seconds) used as the window anchor.
        window: Duration in seconds of the sliding window (default 10).
        limit: Maximum number of actions permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the sensor may act and *remaining* is the number of actions still
        available within the current window.

    Raises:
        ValueError: If *window* is outside the supported range.
    """
    _validate_window(window)

    cutoff = now - window
    active = _compute_active_timestamps(timestamps, cutoff)

    _log.debug("sensor check: %d active actions in window", len(active))

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
