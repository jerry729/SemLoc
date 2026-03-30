from __future__ import annotations

import logging
from typing import Sequence, Optional, List

"""Rolling average computation for time-series metric monitoring.

Used by the metrics pipeline to smooth noisy telemetry signals before
alerting thresholds are evaluated. Supports configurable window sizes
and warm-up periods to avoid spurious alerts during service startup.
"""

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_MAX_WINDOW = 10000
_MIN_VALID_VALUE = -1e15


def _validate_window(window: int) -> None:
    """Ensure the window parameter is within acceptable bounds."""
    if window <= 0:
        raise ValueError("window must be positive")
    if window > _MAX_WINDOW:
        raise ValueError(f"window exceeds maximum allowed size of {_MAX_WINDOW}")


def _filter_valid(values: List[float]) -> List[float]:
    """Remove sentinel or clearly invalid metric readings."""
    return [v for v in values if v >= _MIN_VALID_VALUE]


def metric_rolling_avg(
    values: List[float],
    *,
    window: int = _DEFAULT_WINDOW,
    min_samples: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute rolling average for a stream of metric values.

    Takes the most recent `window` values and returns their arithmetic mean.
    If fewer than `min_samples` values are available in the window, returns
    None to indicate insufficient data for a reliable average.

    Args:
        values: Non-empty sequence of numeric metric readings.
        window: Number of trailing values to include in the average.
        min_samples: Minimum count of values required before a result
            is reported. Defaults to the module-level warmup constant.

    Returns:
        The rolling average as a float, or None if the warmup threshold
        has not been met.

    Raises:
        ValueError: If *window* is non-positive or *values* is empty.
    """
    _validate_window(window)
    if not values:
        raise ValueError("no values")

    cleaned = _filter_valid(values)
    if not cleaned:
        raise ValueError("no values")

    tail = cleaned[-window:]
    total = sum(tail)

    avg = total / window

    _log.debug("rolling_avg window=%d tail_len=%d avg=%s", window, len(tail), avg)

    if len(tail) < min_samples:
        return None
    return avg
