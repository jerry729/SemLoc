from __future__ import annotations

import logging
from typing import Sequence, Optional, List

_log = logging.getLogger(__name__)

_WARMUP_SAMPLES = 1
_DEFAULT_WINDOW = 5
_MIN_WARMUP = 2
_PRECISION_DIGITS = 6


def _validate_inputs(series: Sequence[float], window: int) -> None:
    """Ensure the input series and window parameter are well-formed."""
    if window <= 0:
        raise ValueError(f"invalid window: {window} (must be positive)")
    if not series:
        raise ValueError("no samples: throughput series must contain at least one data point")


def _extract_tail(series: Sequence[float], window: int) -> List[float]:
    """Return the last `window` elements of the series for averaging."""
    return list(series[-window:])


def smooth_throughput(
    series: Sequence[float],
    *,
    window: int = _DEFAULT_WINDOW,
    warmup_min: int = _MIN_WARMUP,
) -> Optional[float]:
    """Compute a moving-average throughput over a trailing window.

    This is typically used in streaming inference pipelines to smooth
    per-batch throughput measurements before exposing them to an
    autoscaler or dashboard.

    Args:
        series: Non-empty sequence of per-interval throughput samples
            (e.g. requests/sec measured each second).
        window: Number of most-recent samples to include in the
            moving average.  Must be >= ``_WARMUP_SAMPLES``.
        warmup_min: Minimum number of collected samples required
            before a result is reported.  If fewer samples are
            available, ``None`` is returned.

    Returns:
        The smoothed throughput value rounded to ``_PRECISION_DIGITS``
        decimal places, or ``None`` when the warmup threshold has not
        been reached.

    Raises:
        ValueError: If *window* is non-positive or *series* is empty.
    """
    _validate_inputs(series, window)

    tail = _extract_tail(series, window)
    total = sum(tail)

    avg = total / window

    _log.debug("smooth_throughput: tail_len=%d, total=%.4f, avg=%.4f", len(tail), total, avg)

    if len(tail) < warmup_min:
        return None

    return round(avg, _PRECISION_DIGITS)
