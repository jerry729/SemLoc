from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 0.0
INTERPOLATION_ORIGIN = 1.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the demand segment has non-zero horizontal extent."""
    if x1 == x0:
        raise ValueError("zero length")


def _interpolate(t: float, y0: float, y1: float) -> float:
    """Linear interpolation between two price/demand endpoints."""
    return (INTERPOLATION_ORIGIN - t) * y0 + t * y1


def demand_curve(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute demand along a line segment defined by two control points.

    The function performs linear interpolation between (x0, y0) and (x1, y1)
    evaluated at the query point *x*. When *clamp* is enabled, the result is
    restricted to lie within the range spanned by the two endpoints so that
    extrapolation beyond the segment is prevented.

    Args:
        x0: Horizontal coordinate of the first control point.
        y0: Demand (vertical) value at the first control point.
        x1: Horizontal coordinate of the second control point.
        y1: Demand (vertical) value at the second control point.
        x: Query coordinate at which to evaluate the demand curve.
        clamp: If ``True`` (default), restrict output to the segment range.

    Returns:
        The interpolated (and optionally clamped) demand value.

    Raises:
        ValueError: If the segment has zero horizontal length (x0 == x1).
    """
    _validate_segment(x0, x1)

    segment_length = x1 - x0
    t = (x - x0) / segment_length
    y = _interpolate(t, y0, y1)

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    _log.debug("demand_curve: x=%s, t=%.4f, y=%.4f, clamped=%s", x, t, y, clamp)
    return y
