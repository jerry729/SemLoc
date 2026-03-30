from __future__ import annotations

import logging
from typing import Sequence, Tuple, List

_log = logging.getLogger(__name__)

"""
Sliding-window rate limiter for query endpoints.

Used by API gateway middleware to enforce per-client query rate limits
before requests reach downstream services. The window is defined in
seconds and the limit represents the maximum allowed queries per window.
"""

DEFAULT_WINDOW_SECONDS: int = 10
DEFAULT_QUERY_LIMIT: int = 5
MIN_WINDOW_SECONDS: int = 1
MIN_LIMIT: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure rate-limit parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be >= {MIN_WINDOW_SECONDS}, got {window}"
        )
    if limit < MIN_LIMIT:
        raise ValueError(
            f"limit must be >= {MIN_LIMIT}, got {limit}"
        )


def _filter_active(timestamps: Sequence[float], cutoff: float) -> List[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def limit_query(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_QUERY_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window guard that decides whether a new query is permitted.

    Args:
        timestamps: Sequence of UNIX timestamps representing previous queries.
        now: Current UNIX timestamp used as the reference point.
        window: Duration in seconds for the sliding window.
        limit: Maximum number of queries allowed within the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* indicates whether
        the next query may proceed and *remaining* is the number of
        additional queries still available in the current window.

    Raises:
        ValueError: If *window* or *limit* are below their minimums.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    active = _filter_active(timestamps, cutoff)

    _log.debug("active=%d, limit=%d, window=%d", len(active), limit, window)

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
