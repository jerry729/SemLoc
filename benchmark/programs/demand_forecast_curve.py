from __future__ import annotations

import logging
from typing import Sequence, Optional, Tuple

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
INTERPOLATION_TOLERANCE = 1e-12
MAX_FORECAST_HORIZON = 365


def _validate_anchor_points(x0: float, x1: float) -> None:
    """Ensure anchor points are distinct to avoid division by zero."""
    if abs(x1 - x0) < INTERPOLATION_TOLERANCE:
        raise ValueError(
            f"Anchor points must be distinct: x0={x0}, x1={x1}"
        )


def _compute_bounds(y0: float, y1: float) -> Tuple[float, float]:
    """Return the (low, high) demand bounds from the two anchor values."""
    return (min(y0, y1), max(y0, y1))


def demand_forecast_curve(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Estimate demand at a given point using linear interpolation between
    two anchor observations.

    The function is commonly used in supply-chain planning to project
    short-term demand between two known data points on a demand curve.
    When *clamp* is enabled the result is restricted to the range
    defined by the two anchor demand values, preventing extrapolation
    artifacts that could cascade into downstream inventory decisions.

    Args:
        x0: Independent variable at the first anchor (e.g. day index).
        y0: Demand observation at *x0*.
        x1: Independent variable at the second anchor.
        y1: Demand observation at *x1*.
        x: The query point at which to estimate demand.
        clamp: If ``True`` (default), restrict the output to
            ``[min(y0, y1), max(y0, y1)]``.

    Returns:
        Estimated demand value at *x*.

    Raises:
        ValueError: If *x0* equals *x1* (degenerate segment).
    """
    _validate_anchor_points(x0, x1)

    ratio = (x - x0) / (x1 - x0)
    y = y0 + ratio * (y1 - y0)

    _log.debug("Interpolation ratio=%.4f, raw forecast=%.4f", ratio, y)

    if not clamp:
        low, high = _compute_bounds(y0, y1)
        if y < low:
            y = low
        elif y > high:
            y = high
    return y
