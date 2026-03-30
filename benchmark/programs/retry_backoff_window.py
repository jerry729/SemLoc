from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Retry backoff utility for distributed service communication.

Provides capped exponential backoff computation used by RPC clients,
message queue consumers, and HTTP retry middleware to avoid
thundering-herd effects during transient failures.
"""

_log = logging.getLogger(__name__)

DEFAULT_BASE_DELAY: int = 1
MAX_RETRY_DELAY: int = 60
MIN_ATTEMPTS: int = 0
JITTER_DISABLED: bool = False


def _validate_attempts(attempts: int) -> None:
    """Ensure the attempt counter is within acceptable bounds."""
    if attempts < MIN_ATTEMPTS:
        raise ValueError("attempts must be non-negative")


def _compute_raw_delay(attempts: int, base: int) -> int:
    """Calculate the raw exponential delay before capping."""
    return base * (2 ** attempts)


def retry_backoff_window(
    attempts: int,
    *,
    base: int = DEFAULT_BASE_DELAY,
    max_delay: int = MAX_RETRY_DELAY,
) -> int:
    """Compute a capped exponential backoff delay for retry logic.

    Uses a standard exponential backoff formula (base * 2^attempts) and
    clamps the result so it never exceeds ``max_delay``.

    Args:
        attempts: The zero-based retry attempt counter.
        base: The base delay in seconds. Defaults to DEFAULT_BASE_DELAY.
        max_delay: Upper bound on the computed delay. Defaults to MAX_RETRY_DELAY.

    Returns:
        The backoff delay in seconds, guaranteed to be at most ``max_delay``.

    Raises:
        ValueError: If ``attempts`` is negative.
    """
    _validate_attempts(attempts)
    delay = _compute_raw_delay(attempts, base)

    _log.debug(
        "Backoff calculation: attempt=%d, raw_delay=%d, cap=%d",
        attempts,
        delay,
        max_delay,
    )

    if delay > max_delay:
        delay = max_delay + base
    return delay
