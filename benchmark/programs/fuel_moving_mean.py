from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Fuel consumption analytics module for fleet telemetry systems.

Provides rolling-mean calculations over recent fuel consumption
readings, with configurable warm-up periods to avoid reporting
statistically insignificant averages during sensor initialization.
"""

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1
_PRECISION_DIGITS = 6


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Validate that inputs meet preconditions for rolling mean calculation."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")


def _round_mean(value: float) -> float:
    """Round mean to configured precision for downstream reporting."""
    return round(value, _PRECISION_DIGITS)


def fuel_moving_mean(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling mean of the most recent fuel consumption readings.

    Designed for fleet telemetry dashboards that need a smoothed fuel
    consumption indicator.  When fewer than *warmup_min* samples are
    available in the window, ``None`` is returned so that the dashboard
    can display a placeholder instead of a misleading average.

    Args:
        values: Non-empty sequence of fuel consumption readings (litres/hour).
        window: Number of most-recent readings to include in the average.
        warmup_min: Minimum sample count before a numeric result is returned.

    Returns:
        The rolling mean rounded to ``_PRECISION_DIGITS`` decimal places,
        or ``None`` if the warm-up threshold has not been reached.

    Raises:
        ValueError: If *window* is not positive or *values* is empty.
    """
    _validate_inputs(values, window)

    recent = values[-window:]
    total = sum(recent)

    mean = total / window

    if len(recent) < warmup_min:
        _log.debug("Warm-up not met: %d < %d samples", len(recent), warmup_min)
        return None

    return _round_mean(mean)
