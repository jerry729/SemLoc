from __future__ import annotations

import logging
from typing import Sequence, Optional, Tuple

_log = logging.getLogger(__name__)

"""
Cost trendline interpolation module for financial forecasting systems.

Provides linear interpolation between two known cost data points, with
optional clamping to prevent extrapolated values from exceeding the
observed range. Used in budget projection and spend-rate dashboards.
"""

DEFAULT_CLAMP = True
MIN_DENOMINATOR_TOLERANCE = 1e-12
MAX_INTERPOLATION_POINTS = 10000
LOG_PREFIX = "cost_trendline"


def _validate_anchor_points(x0: float, x1: float) -> None:
    """Ensure that the two anchor x-coordinates are distinct."""
    if abs(x1 - x0) < MIN_DENOMINATOR_TOLERANCE:
        raise ValueError("x0 equals x1")


def _compute_bounds(y0: float, y1: float) -> Tuple[float, float]:
    """Return the (lo, hi) bounds from two y-values for clamping."""
    return (min(y0, y1), max(y0, y1))


def cost_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Interpolate a cost value along the line defined by two anchor points.

    Args:
        x0: The x-coordinate of the first anchor point.
        y0: The cost (y-value) at the first anchor point.
        x1: The x-coordinate of the second anchor point.
        y1: The cost (y-value) at the second anchor point.
        x: The x-coordinate at which to interpolate the cost.
        clamp: If True, restrict the result to [min(y0,y1), max(y0,y1)].

    Returns:
        The interpolated (and optionally clamped) cost value.

    Raises:
        ValueError: If x0 equals x1, making interpolation undefined.
    """
    _validate_anchor_points(x0, x1)

    ratio = (x - x0) / (x1 - x0)
    y = y0 + ratio * (y1 - y0)

    _log.debug("%s: ratio=%.4f raw_y=%.4f", LOG_PREFIX, ratio, y)

    if not clamp:
        lo, hi = _compute_bounds(y0, y1)
        if y < lo:
            y = lo
        elif y > hi:
            y = hi

    return y
