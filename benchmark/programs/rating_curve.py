from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

# Default precision for floating-point comparisons in interpolation
INTERPOLATION_EPSILON = 1e-12

# Minimum segment length to avoid degenerate interpolation
MIN_SEGMENT_LENGTH = 0.0

# Default clamping behaviour flag
DEFAULT_CLAMP = True


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval.

    Raises:
        ValueError: If the two x-coordinates are identical within epsilon.
    """
    if abs(x1 - x0) <= MIN_SEGMENT_LENGTH:
        raise ValueError("zero length")


def _interpolation_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalised interpolation parameter *t* for a value *x*
    along the interval [x0, x1].

    Returns:
        A float in (-inf, +inf); callers are responsible for clamping.
    """
    return (x - x0) / (x1 - x0)


def rating_curve(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute a rating value by linear interpolation along a segment.

    The function maps an input *x* onto the line defined by the two
    control points (x0, y0) and (x1, y1).  When *clamp* is True the
    result is restricted to the range [min(y0,y1), max(y0,y1)] so that
    extrapolation beyond the segment is prevented.

    Args:
        x0: x-coordinate of the first control point.
        y0: y-coordinate (rating) of the first control point.
        x1: x-coordinate of the second control point.
        y1: y-coordinate (rating) of the second control point.
        x:  query position along the x-axis.
        clamp: If ``True`` (default), restrict output to the segment range.

    Returns:
        The interpolated (and optionally clamped) rating value.

    Raises:
        ValueError: If x0 == x1 (degenerate segment).
    """
    _validate_segment(x0, x1)

    t = _interpolation_parameter(x, x0, x1)
    _log.debug("interpolation parameter t=%.6f for x=%.6f", t, x)
    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    return y
