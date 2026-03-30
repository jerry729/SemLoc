from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
CAP_OVERFLOW_MSG: str = "Counter for key '%s' clamped at cap %d"
MIN_CAP_VALUE: int = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value, if provided, is within acceptable bounds."""
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _ensure_key_exists(counters: Dict[str, int], key: str) -> None:
    """Initialize the counter for a key if it does not already exist."""
    counters.setdefault(key, DEFAULT_INITIAL_COUNT)


def bump_job(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Increment a job-execution counter and enforce an optional hard cap.

    This is used by the scheduler to track how many times a particular job
    has been dispatched within a scheduling window.  When a *cap* is
    supplied the counter will never exceed that value, preventing runaway
    re-execution of flaky or misbehaving jobs.

    Args:
        counters: Mutable mapping of job keys to their current counts.
        key: Identifier for the job whose counter should be bumped.
        cap: Optional upper bound for the counter.  When ``None``, the
            counter grows without limit.

    Returns:
        The counter value for *key* after the bump (and possible clamping).

    Raises:
        ValueError: If *cap* is provided but is less than ``MIN_CAP_VALUE``.
    """
    _validate_cap(cap)
    _ensure_key_exists(counters, key)

    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1
        _log.debug(CAP_OVERFLOW_MSG, key, cap)

    return counters[key]
