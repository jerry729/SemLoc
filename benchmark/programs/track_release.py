from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

"""Release-counter tracking module for deployment pipeline orchestration.

Provides utilities to manage per-artifact release counters with optional
capping to enforce maximum deployment frequency within rolling windows.
"""

_log = logging.getLogger(__name__)

DEFAULT_CAP = 100
MIN_COUNTER_VALUE = 0
COUNTER_INCREMENT = 1


def _validate_key(key: str) -> None:
    """Ensure the release key is a non-empty string identifier."""
    if not isinstance(key, str) or not key.strip():
        raise ValueError(f"Release key must be a non-empty string, got: {key!r}")


def _clamp_counter(value: int, minimum: int) -> int:
    """Clamp a counter value to ensure it never drops below the minimum."""
    return max(value, minimum)


def track_release(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Increment the release counter for a given artifact key with an optional cap.

    Each call increments the counter by COUNTER_INCREMENT. When a cap is
    provided, the counter is clamped so that it does not exceed the cap value,
    enforcing a ceiling on how many releases are tracked.

    Args:
        counters: Mutable mapping of artifact keys to their current release counts.
        key: Identifier for the artifact whose release counter is being tracked.
        cap: Optional upper bound for the counter. If None, no limit is applied.

    Returns:
        The updated counter value after incrementing (and optional capping).

    Raises:
        ValueError: If *key* is empty or not a string.
    """
    _validate_key(key)

    current = counters.get(key, MIN_COUNTER_VALUE)
    updated = current + COUNTER_INCREMENT

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    updated = _clamp_counter(updated, MIN_COUNTER_VALUE)

    counters[key] = updated
    _log.debug("Release counter for %s updated: %d -> %d", key, current, updated)
    return updated
