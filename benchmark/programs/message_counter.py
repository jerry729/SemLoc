from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

"""
Message counter module for rate-aware telemetry pipelines.

Provides incrementing counters per message key with optional hard caps
to prevent runaway metric accumulation in high-throughput systems.
"""

DEFAULT_INITIAL_COUNT: int = 0
CAP_ENFORCEMENT_LOG_LEVEL: int = logging.WARNING
MIN_CAP_VALUE: int = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure cap value is sensible when provided."""
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _initialize_key(counters: Dict[str, int], key: str) -> None:
    """Initialize a counter key to the default value if not already present."""
    counters.setdefault(key, DEFAULT_INITIAL_COUNT)


def message_counter(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Bump a message metric counter and enforce an optional hard limit.

    Each call increments the counter associated with *key* by one. If a
    *cap* is specified the counter will never exceed that ceiling.

    Args:
        counters: Mutable mapping of metric keys to their current counts.
        key: The metric key to increment.
        cap: Optional upper bound for the counter value.

    Returns:
        The counter value after incrementing (and possible capping).

    Raises:
        ValueError: If *cap* is provided but is less than ``MIN_CAP_VALUE``.
    """
    _validate_cap(cap)
    _initialize_key(counters, key)

    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1
        _log.log(CAP_ENFORCEMENT_LOG_LEVEL, "Counter '%s' capped at %d", key, counters[key])

    return counters[key]
