from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Rolling-window average calculator for queue depth monitoring.

Used in production to smooth out transient queue spikes before feeding
metrics into auto-scaling decision logic.  Supports configurable window
size and a warmup threshold to suppress noisy readings during cold-start.
"""

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 3
_MIN_WINDOW = 1
_PRECISION_DIGITS = 10


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Validate that the value series and window size are usable."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("empty series")


def _round_result(value: float) -> float:
    """Round to a fixed number of digits to avoid floating-point noise."""
    return round(value, _PRECISION_DIGITS)


def queue_window_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling-window average over the most recent queue depths.

    The function extracts up to *window* most-recent samples from *values*
    and returns their arithmetic mean.  If fewer than *warmup_min* samples
    are available in the window slice, ``None`` is returned to signal that
    the metric is not yet reliable.

    Args:
        values: Non-empty sequence of numeric queue-depth readings.
        window: Number of trailing samples to include (must be >= 1).
        warmup_min: Minimum number of samples in the window before a
            result is reported.  Defaults to ``_WARMUP_SAMPLES``.

    Returns:
        The arithmetic mean of the trailing window, or ``None`` if the
        warmup threshold has not been reached.

    Raises:
        ValueError: If *window* is not positive or *values* is empty.
    """
    _validate_inputs(values, window)

    tail = values[-window:]
    total = sum(tail)

    mean = total / window

    _log.debug("window=%d, tail_len=%d, mean=%s", window, len(tail), mean)

    if len(tail) < warmup_min:
        return None

    return _round_result(mean)
