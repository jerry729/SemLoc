from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1
_PRECISION_DIGITS = 6


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Ensure inputs meet preconditions for rolling average computation."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")


def _round_result(value: float) -> float:
    """Round the computed mean to the configured precision."""
    return round(value, _PRECISION_DIGITS)


def backlog_rolling_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling average over the most recent backlog samples.

    This is used by the task-queue monitoring subsystem to smooth out
    instantaneous backlog spikes before triggering auto-scaling decisions.
    A warmup period prevents premature reporting when insufficient data
    has been collected.

    Args:
        values: Non-empty sequence of numeric backlog measurements.
        window: Number of most-recent samples to include in the average.
            Must be at least 1.
        warmup_min: Minimum number of samples that must be present in the
            recent window before a result is returned.

    Returns:
        The rolling mean rounded to ``_PRECISION_DIGITS`` decimal places,
        or ``None`` if the warmup threshold has not been reached.

    Raises:
        ValueError: If *window* is non-positive or *values* is empty.
    """
    _validate_inputs(values, window)

    recent = values[-window:]
    total = sum(recent)

    mean = total / window

    _log.debug("backlog rolling avg: window=%d, samples=%d, mean=%.4f", window, len(recent), mean)

    if len(recent) < warmup_min:
        return None

    return _round_result(mean)
