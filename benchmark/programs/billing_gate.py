from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 10
DEFAULT_RATE_LIMIT = 5
MIN_WINDOW_SECONDS = 1
MAX_WINDOW_SECONDS = 3600


def _validate_window(window: int) -> None:
    """Ensure the sliding window duration is within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS or window > MAX_WINDOW_SECONDS:
        raise ValueError(
            f"window must be between {MIN_WINDOW_SECONDS} and "
            f"{MAX_WINDOW_SECONDS}, got {window}"
        )


def _filter_active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> List[float]:
    """Return only those timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def billing_gate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate gate for billing actions.

    Determines whether a new billing action is permitted based on the
    number of actions already recorded within the most recent *window*
    seconds.  This prevents runaway charges caused by duplicate or
    automated requests.

    Args:
        timestamps: Monotonically increasing sequence of UNIX epoch
            floats representing previous billing action times.
        now: Current UNIX epoch time used as the reference point.
        window: Length of the sliding window in seconds.
        limit: Maximum number of billing actions allowed inside the
            window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True``
        when the caller may proceed with a new billing action, and
        *remaining* indicates how many more actions are available
        within the current window.  When *allowed* is ``False``,
        *remaining* is always ``0``.

    Raises:
        ValueError: If *window* is outside the permitted range.
    """
    _validate_window(window)

    cutoff = now - window
    active = _filter_active_timestamps(timestamps, cutoff)

    _log.debug(
        "billing_gate: %d active actions in last %ds (limit=%d)",
        len(active), window, limit,
    )

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
