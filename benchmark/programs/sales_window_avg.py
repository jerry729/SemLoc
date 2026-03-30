from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Rolling sales-window averaging module.

Provides utilities for computing rolling averages over recent sales
figures, with configurable window sizes and warmup periods to avoid
reporting unreliable statistics from insufficient data.
"""

_log = logging.getLogger(__name__)
_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 4
_MIN_WINDOW = 1


def _validate_inputs(values: Sequence[float], window: int) -> None:
    """Validate that inputs meet basic preconditions.

    Raises:
        ValueError: If window is non-positive or values is empty.
    """
    if window < _MIN_WINDOW:
        raise ValueError("window must be positive")
    if not values:
        raise ValueError("no values")


def _extract_recent(values: Sequence[float], window: int) -> list[float]:
    """Return the most recent `window` values from the sequence.

    If fewer than `window` values exist, returns all available values.
    """
    return list(values[-window:])


def sales_window_avg(
    values: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _WARMUP_SAMPLES,
) -> Optional[float]:
    """Compute the rolling mean over the most recent sales figures.

    Uses a trailing window to compute an average of recent sales data.
    If the number of available samples is below the warmup threshold,
    returns ``None`` to indicate insufficient data.

    Args:
        values: Non-empty sequence of numeric sales figures.
        window: Number of recent periods to include in the average.
        warmup_min: Minimum number of samples required before a
            meaningful average can be returned.

    Returns:
        The rolling mean as a float, or ``None`` if the warmup
        threshold has not been met.

    Raises:
        ValueError: If *window* is not positive or *values* is empty.
    """
    _validate_inputs(values, window)

    recent = _extract_recent(values, window)
    total = sum(recent)

    _log.debug("Window=%d, recent_count=%d, total=%.2f", window, len(recent), total)

    mean = total / window

    if len(recent) < warmup_min:
        return None
    return mean
