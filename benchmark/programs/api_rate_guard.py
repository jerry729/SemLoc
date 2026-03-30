from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

"""
API Rate Guard Module

Provides a lightweight, in-process rate limiter for outbound API calls.
Designed for use in microservice gateways where distributed rate limiting
is not required but per-instance throttling must be enforced.
"""

DEFAULT_WINDOW_SECONDS: int = 60
DEFAULT_REQUEST_LIMIT: int = 100
MIN_WINDOW_SECONDS: int = 1
MIN_LIMIT: int = 1


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure rate-guard parameters are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be >= {MIN_WINDOW_SECONDS}, got {window}"
        )
    if limit < MIN_LIMIT:
        raise ValueError(
            f"limit must be >= {MIN_LIMIT}, got {limit}"
        )


def _filter_recent(timestamps: Sequence[float], cutoff: float) -> list[float]:
    """Return only timestamps that fall on or after the cutoff."""
    return [t for t in timestamps if t >= cutoff]


def api_rate_guard(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_REQUEST_LIMIT,
) -> Tuple[bool, int]:
    """Determine whether an API call is permitted under the current rate window.

    Args:
        timestamps: Monotonically-ordered sequence of previous request epochs.
        now: The current epoch timestamp (seconds).
        window: Length of the sliding window in seconds.
        limit: Maximum number of requests allowed within *window*.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` when the
        caller may proceed, and *remaining* is the number of requests still
        available in the current window (``0`` when denied).

    Raises:
        ValueError: If *window* or *limit* is below the minimum threshold.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent(timestamps, cutoff)

    _log.debug(
        "rate_guard: %d recent requests in last %ds (limit=%d)",
        len(recent), window, limit,
    )

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
