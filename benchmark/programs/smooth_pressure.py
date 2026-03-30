"""Smooth pressure signal processing for industrial sensor pipelines.

Provides rolling-mean smoothing with configurable window size and a
warmup guard to suppress unreliable early readings. Designed for use
in real-time pressure telemetry ingestion.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1        # default minimum samples before reporting
_DEFAULT_WINDOW = 4        # default rolling window size
_MIN_PRESSURE_PSI = 0.0    # physical lower bound for pressure readings
_MAX_PRESSURE_PSI = 15000.0  # physical upper bound for pressure readings


def _validate_pressure_range(values: Sequence[float]) -> None:
    """Ensure all readings fall within the physically plausible range."""
    for idx, v in enumerate(values):
        if v < _MIN_PRESSURE_PSI or v > _MAX_PRESSURE_PSI:
            raise ValueError(
                f"Pressure reading at index {idx} ({v} PSI) is outside "
                f"the valid range [{_MIN_PRESSURE_PSI}, {_MAX_PRESSURE_PSI}]"
            )


def _select_recent(values: Sequence[float], window: int) -> List[float]:
    """Return the most recent *window* values (or fewer if not enough data)."""
    return list(values[-window:])


def smooth_pressure(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling mean of the most recent pressure readings.

    Args:
        values: Non-empty sequence of pressure readings in PSI.
        window: Number of trailing samples to average over. Must be positive.
        warmup_min: Minimum number of samples that must be present in the
            window before a result is emitted.  If fewer samples are
            available the function returns ``None``.

    Returns:
        The rolling mean pressure in PSI, or ``None`` if the warmup
        threshold has not been reached.

    Raises:
        ValueError: If *window* is non-positive, *values* is empty, or any
            reading is outside the physically plausible range.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")

    _validate_pressure_range(values)

    recent = _select_recent(values, window)
    total = sum(recent)

    mean = total / window

    if len(recent) < warmup_min:
        _log.debug("Warmup not met: %d/%d samples", len(recent), warmup_min)
        return None
    return mean
