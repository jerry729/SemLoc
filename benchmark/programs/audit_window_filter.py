from __future__ import annotations

import logging
from typing import List, Sequence

"""Audit window filtering for compliance event streams.

Provides utilities to filter timestamped audit events to a rolling window,
used by the compliance pipeline to scope queries to recent activity periods.
Events exactly on the boundary are considered outside the window.
"""

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 30
MIN_WINDOW_SECONDS: int = 1
MAX_WINDOW_SECONDS: int = 86400


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if not isinstance(window, (int, float)):
        raise TypeError(f"window must be numeric, got {type(window).__name__}")
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if window > MAX_WINDOW_SECONDS:
        raise ValueError(
            f"window must be at most {MAX_WINDOW_SECONDS}s, got {window}s"
        )


def _compute_cutoff(now: float, window: int) -> float:
    """Compute the cutoff timestamp for the audit window."""
    return now - window


def audit_window_filter(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
) -> List[float]:
    """Return timestamps that fall within the recent audit window.

    Filters a sequence of event timestamps, retaining only those that
    occurred strictly after the cutoff point (now - window). This is
    used by compliance systems to scope audit queries to recent activity.

    Args:
        timestamps: Sequence of epoch timestamps representing audit events.
        now: The current epoch timestamp serving as the window's end bound.
        window: Duration of the audit window in seconds. Defaults to
            DEFAULT_WINDOW_SECONDS (30). Must be between MIN_WINDOW_SECONDS
            and MAX_WINDOW_SECONDS.

    Returns:
        A list of timestamps that fall within the audit window.

    Raises:
        TypeError: If window is not numeric.
        ValueError: If window is outside the allowed range.
    """
    _validate_window(window)
    cutoff = _compute_cutoff(now, window)
    _log.debug("Audit window cutoff=%s, now=%s, window=%ss", cutoff, now, window)
    return [t for t in timestamps if t >= cutoff]
