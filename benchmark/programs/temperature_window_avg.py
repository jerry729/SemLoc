"""Temperature smoothing utilities for IoT sensor pipelines.

Provides rolling-window averaging with configurable warmup semantics,
designed for thermostat and HVAC telemetry streams where early readings
may be unreliable until a minimum number of samples have been collected.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1          # default minimum samples before reporting
_DEFAULT_WINDOW = 3          # default rolling window width
_MIN_WINDOW = 1              # smallest legal window size
_ABSOLUTE_ZERO_C = -273.15   # physical lower bound for sanity checks


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")


def _validate_series(values: Sequence[float]) -> None:
    """Reject empty or obviously corrupt temperature series."""
    if not values:
        raise ValueError("empty series")
    for v in values:
        if v < _ABSOLUTE_ZERO_C:
            raise ValueError(
                f"temperature {v} below absolute zero ({_ABSOLUTE_ZERO_C} °C)"
            )


def temperature_window_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling-window mean of the most recent temperature readings.

    Args:
        values: Non-empty sequence of temperature values in degrees Celsius,
            ordered chronologically.
        window: Number of trailing samples to include in the average.
        warmup_min: Minimum number of samples that must be present in the
            window before a result is reported.  If fewer samples are
            available, ``None`` is returned.

    Returns:
        The arithmetic mean of the trailing *window* samples, or ``None``
        when the warmup threshold has not been met.

    Raises:
        ValueError: If *window* is not positive or *values* is empty or
            contains temperatures below absolute zero.
    """
    _validate_window(window)
    _validate_series(values)

    tail = values[-window:]
    total = sum(tail)

    mean = total / window

    _log.debug("window=%d, tail_len=%d, mean=%.4f", window, len(tail), mean)

    if len(tail) < warmup_min:
        return None
    return mean
