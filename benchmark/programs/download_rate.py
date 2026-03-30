from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants for the sliding-window rate limiter
# ---------------------------------------------------------------------------
DEFAULT_WINDOW_SECONDS: int = 10
DEFAULT_DOWNLOAD_LIMIT: int = 5
MIN_WINDOW_SECONDS: int = 1
MAX_TIMESTAMP_DRIFT: float = 0.5


def _validate_inputs(
    timestamps: Sequence[float], now: float, window: int
) -> None:
    """Sanity-check arguments before applying the rate-limit logic."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"window must be >= {MIN_WINDOW_SECONDS}, got {window}"
        )
    for ts in timestamps:
        if ts > now + MAX_TIMESTAMP_DRIFT:
            raise ValueError(
                f"Timestamp {ts} is too far in the future (now={now}, "
                f"max drift={MAX_TIMESTAMP_DRIFT})"
            )


def _active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only those timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def download_rate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_DOWNLOAD_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window guard for download actions.

    Determines whether a new download is permitted based on how many
    downloads have already occurred within the most recent *window*
    seconds.

    Args:
        timestamps: Recorded UTC timestamps of previous downloads.
        now: The current UTC timestamp.
        window: Length of the sliding window in seconds.
        limit: Maximum number of downloads allowed inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True``
        when the caller may proceed and *remaining* is the number of
        downloads still available in the current window.

    Raises:
        ValueError: If *window* is below the minimum or a timestamp
            lies unreasonably far in the future.
    """
    _validate_inputs(timestamps, now, window)

    cutoff = now - window
    active = _active_timestamps(timestamps, cutoff)

    _log.debug("active=%d, limit=%d, window=%d", len(active), limit, window)

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
