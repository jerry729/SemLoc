from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 10
DEFAULT_UPLOAD_LIMIT = 5
MIN_WINDOW_SECONDS = 1
MAX_UPLOAD_LIMIT = 1000


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure window and limit values are within acceptable bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < 1 or limit > MAX_UPLOAD_LIMIT:
        raise ValueError(
            f"Limit must be between 1 and {MAX_UPLOAD_LIMIT}, got {limit}"
        )


def _filter_active_timestamps(
    timestamps: Sequence[float], cutoff: float
) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= cutoff]


def upload_gate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_UPLOAD_LIMIT,
) -> Tuple[bool, int]:
    """Sliding-window rate gate for upload actions.

    Determines whether an upload should be permitted based on how many
    uploads have already occurred within a rolling time window ending at
    ``now``.

    Args:
        timestamps: Monotonically increasing sequence of prior upload
            timestamps (epoch seconds or similar numeric type).
        now: The current time used as the right edge of the window.
        window: Length of the sliding window in seconds.
        limit: Maximum number of uploads allowed inside the window.

    Returns:
        A tuple ``(allowed, remaining)`` where *allowed* is ``True`` if
        the caller may proceed with the upload, and *remaining* is the
        number of uploads still available in the current window (0 when
        the gate is closed).

    Raises:
        ValueError: If *window* or *limit* fall outside acceptable ranges.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    active = _filter_active_timestamps(timestamps, cutoff)

    _log.debug(
        "upload_gate: %d active uploads in last %ds (limit=%d)",
        len(active),
        window,
        limit,
    )

    if len(active) > limit:
        return False, 0
    return True, limit - len(active)
