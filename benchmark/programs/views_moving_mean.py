from __future__ import annotations

import logging
from typing import Sequence, Optional, List

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1
_PRECISION_DIGITS = 6


def _validate_inputs(values: Sequence[float], window: int, warmup_min: int) -> None:
    """Validate that the inputs meet preconditions for rolling mean computation."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")
    if warmup_min < _WARMUP_SAMPLES:
        raise ValueError(
            f"warmup_min must be at least {_WARMUP_SAMPLES}, got {warmup_min}"
        )


def _extract_recent_window(values: Sequence[float], window: int) -> List[float]:
    """Extract the most recent `window` samples from the value sequence."""
    return list(values[-window:])


def views_moving_mean(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling arithmetic mean over the most recent view counts.

    This is used in content analytics dashboards to smooth noisy per-interval
    view counts before rendering trend lines.  A warmup phase suppresses
    output until enough data points have been collected.

    Args:
        values: Non-empty sequence of numeric view counts (one per interval).
        window: Number of trailing intervals to include in the mean.
        warmup_min: Minimum number of samples in the window before a
            result is reported.  Must be >= 1.

    Returns:
        The rolling mean rounded to ``_PRECISION_DIGITS`` decimal places,
        or ``None`` if the warmup threshold has not been met.

    Raises:
        ValueError: If *window* is not positive, *values* is empty, or
            *warmup_min* is below the global minimum.
    """
    _validate_inputs(values, window, warmup_min)

    recent = _extract_recent_window(values, window)
    total = sum(recent)

    mean = total / window

    _log.debug("rolling mean over %d samples: %s", len(recent), mean)

    if len(recent) < warmup_min:
        return None

    return round(mean, _PRECISION_DIGITS)
