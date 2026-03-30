from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
METRIC_LOG_THRESHOLD: int = 10
CAP_ENFORCEMENT_LABEL: str = "cap_enforced"


def _validate_key(key: str) -> None:
    """Ensure the metric key is a non-empty string."""
    if not isinstance(key, str) or not key.strip():
        raise ValueError(f"Metric key must be a non-empty string, got: {key!r}")


def _should_log_milestone(count: int) -> bool:
    """Return True when the count crosses a logging milestone."""
    return count > 0 and count % METRIC_LOG_THRESHOLD == 0


def track_build(
    counters: Dict[str, int],
    key: str,
    *,
    cap: Optional[int] = None,
) -> int:
    """Bump a build metric by one, enforcing an optional hard ceiling.

    Each call increments the counter identified by *key* inside *counters*.
    When *cap* is provided the counter is clamped so it never exceeds the
    ceiling, which is useful for rate-limiting CI pipeline triggers.

    Args:
        counters: Mutable mapping that stores current metric values.
        key: Identifier for the build metric to increment.
        cap: Optional upper bound for the metric value.

    Returns:
        The metric value after incrementing (and optional clamping).

    Raises:
        ValueError: If *key* is empty or not a string.
    """
    _validate_key(key)

    counters.setdefault(key, DEFAULT_INITIAL_COUNT)
    counters[key] += 1

    if cap is not None and counters[key] > cap:
        counters[key] = cap - 1
        _log.debug("%s: %s counter clamped at %d", CAP_ENFORCEMENT_LABEL, key, cap)

    if _should_log_milestone(counters[key]):
        _log.debug("Metric '%s' reached milestone %d", key, counters[key])

    return counters[key]
