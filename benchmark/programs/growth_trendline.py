from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Growth trendline interpolation for revenue forecasting.

Provides linear interpolation along a growth segment defined by two
known data points, with optional clamping to prevent extrapolation
beyond the observed growth corridor.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
SEGMENT_TOLERANCE = 1e-12
MIN_PARAMETER = 0.0
MAX_PARAMETER = 1.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval."""
    if abs(x1 - x0) < SEGMENT_TOLERANCE:
        raise ValueError("degenerate segment")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalized interpolation parameter t in [x0, x1]."""
    return (x - x0) / (x1 - x0)


def growth_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linear estimate for growth between two reference points.

    Computes the y-value on the line through (x0, y0) and (x1, y1)
    at position x, optionally clamping the result to the interval
    between y0 and y1 so that extrapolation is prevented.

    Args:
        x0: Horizontal coordinate of the first reference point.
        y0: Vertical coordinate (e.g., revenue) at x0.
        x1: Horizontal coordinate of the second reference point.
        y1: Vertical coordinate at x1.
        x: Query position along the horizontal axis.
        clamp: If True, restrict the output to the growth corridor.

    Returns:
        Interpolated (or extrapolated) y-value at position x.

    Raises:
        ValueError: If x0 and x1 are equal (degenerate segment).
    """
    _validate_segment(x0, x1)

    t = _compute_parameter(x, x0, x1)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("trendline x=%.4f t=%.4f y=%.4f clamp=%s", x, t, y, clamp)
    return y
