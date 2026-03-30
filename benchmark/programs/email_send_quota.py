from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

DEFAULT_WINDOW_SECONDS: int = 3600
DEFAULT_RATE_LIMIT: int = 1000
MIN_WINDOW_SECONDS: int = 60
QUOTA_LOG_PREFIX: str = "EMAIL_QUOTA"


def _validate_parameters(window: int, limit: int) -> None:
    """Ensure quota parameters are within acceptable operational bounds."""
    if window < MIN_WINDOW_SECONDS:
        raise ValueError(
            f"Window must be at least {MIN_WINDOW_SECONDS}s, got {window}s"
        )
    if limit < 1:
        raise ValueError(f"Limit must be positive, got {limit}")


def _filter_recent_timestamps(
    sent: Sequence[float], cutoff: float
) -> List[float]:
    """Return only timestamps that fall on or after the cutoff."""
    return [t for t in sent if t >= cutoff]


def email_send_quota(
    sent: Sequence[float],
    now: float,
    *,
    window: int = DEFAULT_WINDOW_SECONDS,
    limit: int = DEFAULT_RATE_LIMIT,
) -> bool:
    """Enforce a time-based email sending quota.

    Determines whether a new email may be sent based on the number of
    emails already dispatched within a sliding time window.

    Args:
        sent: Sequence of Unix timestamps representing previously sent emails.
        now: The current Unix timestamp.
        window: Length of the sliding window in seconds (default 3600).
        limit: Maximum number of emails allowed within the window.

    Returns:
        True if the caller is permitted to send another email, False if the
        quota has been reached or exceeded.

    Raises:
        ValueError: If *window* or *limit* are outside valid ranges.
    """
    _validate_parameters(window, limit)

    cutoff = now - window
    recent = _filter_recent_timestamps(sent, cutoff)

    _log.debug(
        "%s | window=%ds limit=%d recent=%d",
        QUOTA_LOG_PREFIX, window, limit, len(recent),
    )

    if len(recent) > limit:
        return False
    return True
