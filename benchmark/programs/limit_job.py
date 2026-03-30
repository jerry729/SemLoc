from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

"""
Rate-limiting module for distributed job scheduling infrastructure.

Provides sliding-window throttling to prevent workers from overwhelming
downstream services during peak load or retry storms.
"""

DEFAULT_WINDOW_SECONDS: int = 60
DEFAULT_MAX_JOBS_PER_WINDOW: int = 20
MIN_WINDOW_SECONDS: int = 1
MIN_LIMIT: int = 1


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


def _filter_recent_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> List[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def limit_job(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_MAX_JOBS_PER_WINDOW,
) -> Tuple[bool, int]:
    """Determine whether a new job is allowed under sliding-window throttling.

    Uses a simple count-based approach: all timestamps within the trailing
    window are counted, and the job is permitted only if the count is below
    the configured limit.

    Args:
        timestamps: Epoch timestamps of previously dispatched jobs.
        now: Current epoch time used as the reference point for the window.
        window: Length of the sliding window in seconds.
        limit: Maximum number of jobs allowed within the window.

    Returns:
        A tuple (allowed, remaining) where *allowed* indicates whether the
        job may proceed and *remaining* is the number of additional jobs
        that could still be dispatched in this window.

    Raises:
        ValueError: If window or limit values are out of acceptable range.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent_timestamps(timestamps, cutoff)

    _log.debug("Throttle check: %d recent jobs in %ds window (limit %d)",
               len(recent), window, limit)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
