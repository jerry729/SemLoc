from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

"""
Rate-limiting guard for search API endpoints.

Implements a sliding-window algorithm to throttle search requests.
Prevents abuse by limiting how many searches a user can perform
within a configurable time window.
"""

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 10
DEFAULT_RATE_LIMIT: int = 5
MIN_WINDOW_SECONDS: int = 1
MIN_RATE_LIMIT: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure window and limit values are within acceptable bounds."""
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
) -> List[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def guard_search(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Sliding window guard for search actions.

    Determines whether a new search request should be allowed based on
    how many requests have been made within the recent time window.

    Args:
        timestamps: Sequence of UNIX timestamps of previous search requests.
        now: The current UNIX timestamp.
        window: Duration of the sliding window in seconds.
        limit: Maximum number of allowed requests within the window.

    Returns:
        A tuple of (allowed, remaining) where *allowed* indicates whether
        the request may proceed and *remaining* is the number of requests
        still available in the current window.

    Raises:
        ValueError: If window or limit values are below minimum thresholds.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    active = _filter_active_timestamps(timestamps, cutoff)

    _log.debug("guard_search: %d active requests in window", len(active))

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
