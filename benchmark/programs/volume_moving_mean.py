from __future__ import annotations

import logging
from typing import Sequence, Optional, List

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1
_PRECISION_DIGITS = 10


def _validate_inputs(values: Sequence[float], window: int, warmup_min: int) -> None:
    """Validate that inputs meet preconditions for rolling mean computation."""
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")
    if warmup_min < _WARMUP_SAMPLES:
        raise ValueError(f"warmup_min must be at least {_WARMUP_SAMPLES}")


def _extract_recent_window(values: Sequence[float], window: int) -> List[float]:
    """Extract the most recent samples up to the given window size."""
    return list(values[-window:])


def volume_moving_mean(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute a rolling mean over the most recent volume samples.

    Uses a trailing window of the specified size. If fewer samples than
    ``warmup_min`` are available inside the window, the function returns
    ``None`` to signal that the estimate is not yet reliable.

    Args:
        values: Non-empty sequence of volume observations (e.g. trade
            volumes per interval).
        window: Maximum number of trailing samples to include.
        warmup_min: Minimum number of samples required before a mean
            is reported.  Must be >= 1.

    Returns:
        The rolling mean as a float, or ``None`` if the warmup
        threshold has not been met.

    Raises:
        ValueError: If *window* is not positive or *values* is empty.
    """
    _validate_inputs(values, window, warmup_min)

    recent = _extract_recent_window(values, window)
    total = sum(recent)

    mean = total / window

    _log.debug(
        "volume_moving_mean: window=%d, samples=%d, mean=%s",
        window,
        len(recent),
        round(mean, _PRECISION_DIGITS) if mean is not None else None,
    )

    if len(recent) < warmup_min:
        return None
    return round(mean, _PRECISION_DIGITS)
