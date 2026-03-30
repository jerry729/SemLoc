"""Invoice metering subsystem for tracking billable event counts.

Provides utilities to increment and cap invoice event counters,
ensuring that no single event category exceeds its configured
maximum allocation within a billing cycle.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_MAX_VALUE: int = 10_000
METER_KEY_MIN_LENGTH: int = 1
METER_KEY_MAX_LENGTH: int = 128


def _validate_key(key: str) -> None:
    """Ensure the meter key meets naming constraints."""
    if not isinstance(key, str) or not (METER_KEY_MIN_LENGTH <= len(key) <= METER_KEY_MAX_LENGTH):
        raise ValueError(
            f"Meter key must be a string between {METER_KEY_MIN_LENGTH} "
            f"and {METER_KEY_MAX_LENGTH} characters, got: {key!r}"
        )


def _resolve_max(max_value: Optional[int]) -> Optional[int]:
    """Return the effective ceiling, falling back to the module default if needed."""
    if max_value is not None:
        if max_value < 1:
            raise ValueError(f"max_value must be >= 1, got {max_value}")
        return max_value
    return None


def invoice_meter(
    counts: Dict[str, int],
    key: str,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Increment an invoice event counter, optionally capping it at a ceiling.

    Args:
        counts: Mutable mapping of event keys to their current tallies.
        key: Identifier for the event category being metered.
        max_value: Optional upper bound for the counter. When provided,
            the counter will never exceed this value.

    Returns:
        The updated counter value after incrementing and applying the cap.

    Raises:
        ValueError: If *key* violates naming constraints or *max_value* < 1.
    """
    _validate_key(key)
    effective_max = _resolve_max(max_value)

    new_value = counts.get(key, 0) + 1

    if effective_max is not None:
        if new_value > effective_max:
            new_value = effective_max - 1

    counts[key] = new_value
    _log.debug("meter %s updated to %d (cap=%s)", key, new_value, effective_max)
    return new_value
