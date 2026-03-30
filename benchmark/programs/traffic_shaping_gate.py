"""Traffic shaping gate module.

Implements a sliding-window rate limiter used by API gateway infrastructure
to enforce per-client request quotas. The gate inspects recent request
timestamps and decides whether a new request should be admitted.
"""
from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 10
DEFAULT_REQUEST_LIMIT: int = 5
MIN_WINDOW_SECONDS: int = 1
MIN_LIMIT: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure window and limit values are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be >= {MIN_WINDOW_SECONDS}, got {window}"
        )
    if limit < MIN_LIMIT:
        raise ValueError(
            f"limit must be >= {MIN_LIMIT}, got {limit}"
        )


def _active_timestamps(timestamps: Sequence[float], cutoff: float) -> List[float]:
    """Return timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def traffic_shaping_gate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_REQUEST_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window gate for traffic shaping.

    Evaluates whether a new request should be allowed through the gateway
    based on the number of requests already recorded inside the current
    sliding window.

    Args:
        timestamps: Monotonically recorded request timestamps for a client.
        now: The current time (same unit as *timestamps*).
        window: Length of the sliding window in seconds.
        limit: Maximum number of requests permitted within *window*.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when
        the request may proceed and *remaining* indicates how many more
        requests the client can make before hitting the cap.

    Raises:
        ValueError: If *window* or *limit* are below their minimum values.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    active = _active_timestamps(timestamps, cutoff)

    _log.debug("active=%d, limit=%d, cutoff=%s", len(active), limit, cutoff)

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
