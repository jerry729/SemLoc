from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 0.0
INTERPOLATION_PRECISION = 1e-12


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval."""
    if abs(x1 - x0) <= MIN_SEGMENT_LENGTH:
        raise ValueError("zero length")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalized interpolation parameter t in [x0, x1]."""
    return (x - x0) / (x1 - x0)


def throughput_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute throughput along a linear trend segment between two data points.

    This is used in capacity-planning dashboards to interpolate (and optionally
    extrapolate) throughput between two observed measurement timestamps.

    Args:
        x0: The x-coordinate of the first observation (e.g. epoch seconds).
        y0: The throughput value at *x0* (e.g. requests per second).
        x1: The x-coordinate of the second observation.
        y1: The throughput value at *x1*.
        x: The query point at which to evaluate the trendline.
        clamp: If ``True`` (default), the result is clamped so that the
            interpolation parameter stays within [0, 1], preventing
            extrapolation beyond the observed segment.

    Returns:
        The interpolated (or extrapolated) throughput at *x*.

    Raises:
        ValueError: If *x0* equals *x1*, making the segment degenerate.
    """
    _validate_segment(x0, x1)

    t = _compute_parameter(x, x0, x1)
    _log.debug("interpolation parameter t=%.6f for x=%.4f", t, x)
    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    if abs(y) < INTERPOLATION_PRECISION:
        y = 0.0

    return y
