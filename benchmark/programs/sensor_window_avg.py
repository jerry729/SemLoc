"""Sensor data processing utilities for IoT telemetry pipelines.

Provides rolling-window statistics over raw sensor readings, typically
used in edge gateways to smooth noisy ADC values before upstream
transmission to the cloud aggregation layer.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW_SIZE = 3
_MAX_WINDOW_SIZE = 1024
_EPSILON = 1e-12


def _validate_window(window: int) -> None:
    """Ensure *window* is within the acceptable operational range."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > _MAX_WINDOW_SIZE:
        raise ValueError(
            f"window size {window} exceeds maximum of {_MAX_WINDOW_SIZE}"
        )


def _compute_total(values: Sequence[float]) -> float:
    """Return the sum of *values*, guarding against empty sequences."""
    if not values:
        return 0.0
    return sum(values)


def sensor_window_avg(
    samples: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW_SIZE,
    min_samples: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling mean over the most recent sensor readings.

    Takes the last *window* entries from *samples* and returns their
    arithmetic mean.  If fewer than *min_samples* readings are available
    inside the window the function returns ``None`` to signal that the
    sensor has not warmed up yet.

    Args:
        samples: Non-empty sequence of raw sensor values (volts, °C, etc.).
        window: Number of most-recent samples to consider.
        min_samples: Minimum count of readings required before a mean is
            considered trustworthy.

    Returns:
        The arithmetic mean of the windowed readings, or ``None`` when
        the warmup threshold has not been met.

    Raises:
        ValueError: If *window* is non-positive, exceeds the platform
            maximum, or *samples* is empty.
    """
    _validate_window(window)
    if not samples:
        raise ValueError("no samples")

    recent = samples[-window:]
    total = _compute_total(recent)

    _log.debug("window=%d, recent_count=%d, total=%.4f", window, len(recent), total)

    mean = total / window
    if len(recent) < min_samples:
        return None
    return mean
