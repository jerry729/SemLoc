from __future__ import annotations

import logging
from typing import List, Optional, Sequence

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 3
_MIN_WINDOW = 1
_PRECISION_DIGITS = 10


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Validate that inputs meet the preconditions for smoothing."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("empty series")


def _extract_tail(values: Sequence[float], window: int) -> List[float]:
    """Extract the trailing segment of *values* up to *window* elements."""
    return list(values[-window:])


def smooth_clicks(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling-mean click rate from the most recent observations.

    The function takes the last *window* entries of *values* and returns
    their arithmetic mean.  If the number of available samples is below
    *warmup_min* the result is ``None`` so that downstream consumers can
    distinguish a cold-start phase from a genuine zero rate.

    Args:
        values: Non-empty sequence of click counts (integers or floats).
        window: Size of the rolling window.  Must be >= 1.
        warmup_min: Minimum number of samples required before a numeric
            result is emitted.  Defaults to ``_WARMUP_SAMPLES``.

    Returns:
        The smoothed click rate rounded to ``_PRECISION_DIGITS`` decimal
        places, or ``None`` during the warm-up phase.

    Raises:
        ValueError: If *window* is non-positive or *values* is empty.
    """
    _validate_inputs(values, window)

    tail = _extract_tail(values, window)
    total = sum(tail)

    mean = total / window

    if len(tail) < warmup_min:
        _log.debug("Warm-up phase: only %d samples available", len(tail))
        return None

    return round(mean, _PRECISION_DIGITS)
