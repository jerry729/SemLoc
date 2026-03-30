from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_REQUEST_LIMIT = 20
MIN_WINDOW_SECONDS = 1
MIN_LIMIT = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure that rate-limiting parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be >= {MIN_WINDOW_SECONDS}, got {window}"
        )
    if limit < MIN_LIMIT:
        raise ValueError(
            f"limit must be >= {MIN_LIMIT}, got {limit}"
        )


def _filter_recent(timestamps: Sequence[float], cutoff: float) -> List[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def limit_api(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_REQUEST_LIMIT,
) -> Tuple[bool, int]:
    """Determine whether an API request should be allowed under a sliding-window rate limit.

    The function examines *timestamps* of previous requests and checks how many
    fall within the most recent *window* seconds relative to *now*.  If the
    caller has remaining capacity the request is allowed; otherwise it is
    throttled.

    Args:
        timestamps: Unix-epoch timestamps of previously recorded API calls.
        now: The current Unix-epoch timestamp.
        window: Length of the sliding window in seconds.
        limit: Maximum number of requests permitted inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when the
        request may proceed and *remaining* indicates how many more requests
        the caller can make within the current window.

    Raises:
        ValueError: If *window* or *limit* are below their minimum values.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent(timestamps, cutoff)

    _log.debug("recent=%d, limit=%d, window=%ds", len(recent), limit, window)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
