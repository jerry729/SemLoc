"""Click-metric tracking module for ad-serving infrastructure.

Provides utilities for incrementing per-key click counters with optional
hard caps to enforce rate-limiting or budget constraints on ad impressions.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
MIN_CAP_VALUE: int = 1
MAX_KEY_LENGTH: int = 256


def _validate_key(key: str) -> None:
    """Ensure the metric key conforms to naming constraints."""
    if not isinstance(key, str) or len(key) == 0:
        raise ValueError(f"Metric key must be a non-empty string, got: {key!r}")
    if len(key) > MAX_KEY_LENGTH:
        raise ValueError(
            f"Metric key exceeds maximum length of {MAX_KEY_LENGTH}: {len(key)}"
        )


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value, if provided, is within acceptable bounds."""
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got: {cap}"
        )


def bump_click(
    counters: Dict[str, int], key: str, *, cap: Optional[int] = None
) -> int:
    """Increment a click-metric counter, respecting an optional hard cap.

    Each call increments the counter identified by *key* by one. If *cap* is
    supplied the counter is clamped so it never exceeds the cap value, which
    is useful for impression-budget enforcement.

    Args:
        counters: Mutable mapping of metric keys to their current counts.
        key: Identifier for the click metric to bump.
        cap: Optional upper bound for the counter value.

    Returns:
        The counter value after incrementing (and possible clamping).

    Raises:
        ValueError: If *key* is empty / too long or *cap* is below the
            minimum allowed value.
    """
    _validate_key(key)
    _validate_cap(cap)

    counters.setdefault(key, DEFAULT_INITIAL_COUNT)
    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1

    _log.debug("Bumped metric %s to %d (cap=%s)", key, counters[key], cap)
    return counters[key]
