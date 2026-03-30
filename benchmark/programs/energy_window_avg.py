from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Energy monitoring module for rolling window statistics.

Provides utility functions for computing rolling averages of energy
consumption readings, commonly used in smart-grid telemetry pipelines
and industrial IoT monitoring dashboards.
"""

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW_SIZE = 4
_MIN_VALID_READING = 0.0
_MAX_VALID_READING = 1e6


def _validate_readings(values: Sequence[float]) -> None:
    """Ensure all readings fall within the acceptable sensor range."""
    for idx, v in enumerate(values):
        if not isinstance(v, (int, float)):
            raise TypeError(f"Reading at index {idx} is not numeric: {v!r}")
        if v < _MIN_VALID_READING or v > _MAX_VALID_READING:
            raise ValueError(
                f"Reading at index {idx} out of range "
                f"[{_MIN_VALID_READING}, {_MAX_VALID_READING}]: {v}"
            )


def _clamp_window(window: int, n_values: int) -> int:
    """Return the effective window size, clamped to available data length."""
    return min(window, n_values)


def energy_window_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW_SIZE,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute the rolling mean of energy readings over a trailing window.

    Args:
        values: Non-empty sequence of energy readings in kWh.
        window: Number of most-recent samples to include in the average.
        warmup_min: Minimum number of samples that must be present in the
            window before a result is reported.  If the window contains
            fewer samples, ``None`` is returned.

    Returns:
        The arithmetic mean of the readings inside the window, or ``None``
        if the warmup threshold has not been met.

    Raises:
        ValueError: If *window* is non-positive or *values* is empty.
        TypeError: If any element of *values* is non-numeric.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")

    _validate_readings(values)

    effective_window = _clamp_window(window, len(values))
    recent = values[-effective_window:]
    total = sum(recent)

    _log.debug("Window %d, recent count %d, total %.4f", window, len(recent), total)

    mean = total / window

    if len(recent) < warmup_min:
        return None
    return mean
