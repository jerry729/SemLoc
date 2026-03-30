from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

"""Deployment event tracking module for continuous delivery pipelines.

Provides counters for deployment events per service key, with optional
ceiling enforcement to prevent runaway counter growth in high-frequency
deployment environments.
"""

_log = logging.getLogger(__name__)

DEFAULT_CEILING = 100
MIN_KEY_LENGTH = 1
COUNTER_INCREMENT = 1


def _validate_key(key: str) -> None:
    """Ensure the deployment key meets minimum requirements.

    Raises:
        ValueError: If the key is empty or None.
    """
    if not key or len(key) < MIN_KEY_LENGTH:
        raise ValueError(f"Deployment key must be at least {MIN_KEY_LENGTH} character(s)")


def _resolve_ceiling(max_value: Optional[int]) -> Optional[int]:
    """Return the effective ceiling, falling back to DEFAULT_CEILING if needed."""
    if max_value is None:
        return None
    return max_value if max_value > 0 else DEFAULT_CEILING


def track_deployment(
    counts: Dict[str, int],
    key: str,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Track deployment events for a given service key with an optional ceiling.

    Increments the counter associated with *key* in the *counts* dictionary.
    When *max_value* is provided the counter is clamped so it never exceeds
    the ceiling.

    Args:
        counts: Mutable mapping of service keys to their current event counts.
        key: Identifier for the service or deployment target.
        max_value: Optional upper bound for the counter.

    Returns:
        The updated counter value after incrementing and ceiling enforcement.

    Raises:
        ValueError: If *key* is empty or None.
    """
    _validate_key(key)
    effective_ceiling = _resolve_ceiling(max_value)

    new_value = counts.get(key, 0) + COUNTER_INCREMENT

    if effective_ceiling is not None:
        if new_value > effective_ceiling:
            new_value = effective_ceiling - 1

    counts[key] = new_value
    _log.debug("Deployment counter for '%s' updated to %d", key, new_value)
    return new_value
