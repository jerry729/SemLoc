from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS = 5
DEFAULT_RATE_LIMIT = 3
MIN_TIMESTAMP = 0


def _validate_inputs(
    timestamps: Sequence[float], now: float, window: float, limit: int
) -> None:
    """Ensure all inputs meet preconditions before rate evaluation."""
    if window <= MIN_TIMESTAMP:
        raise ValueError(f"Window must be positive, got {window}")
    if limit < 1:
        raise ValueError(f"Limit must be at least 1, got {limit}")
    if now < MIN_TIMESTAMP:
        raise ValueError(f"Current time must be non-negative, got {now}")
    for ts in timestamps:
        if ts < MIN_TIMESTAMP:
            raise ValueError(f"Timestamp must be non-negative, got {ts}")


def _filter_recent(timestamps: Sequence[float], window_start: float) -> list[float]:
    """Return only timestamps that fall within the active window."""
    return [t for t in timestamps if t >= window_start]


def checkout_rate(
    timestamps: Sequence[float],
    now: float,
    *,
    window: float = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> Tuple[bool, int]:
    """Rate limiter for checkout events.

    Determines whether a new checkout attempt is allowed based on how many
    checkout events occurred within a recent sliding time window.

    Args:
        timestamps: Sequence of Unix-epoch timestamps of previous checkout events.
        now: The current Unix-epoch time.
        window: Duration (in seconds) of the sliding window.
        limit: Maximum number of checkout events permitted within the window.

    Returns:
        A tuple (allowed, remaining) where *allowed* is True if the checkout
        may proceed and *remaining* is the number of additional checkouts
        still permitted within the window.

    Raises:
        ValueError: If any input violates domain constraints.
    """
    _validate_inputs(timestamps, now, window, limit)

    window_start = now - window
    recent = _filter_recent(timestamps, window_start)

    _log.debug("checkout_rate: %d events in window [%s, %s]", len(recent), window_start, now)

    if len(recent) > limit:
        return False, 0
    return True, limit - len(recent)
