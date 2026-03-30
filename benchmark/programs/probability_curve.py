from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Probability curve interpolation module for risk-scoring pipelines.

Provides piecewise-linear interpolation between calibration anchor points,
commonly used in credit-risk and insurance-pricing models to map a continuous
feature value onto a probability scale [0, 1].
"""

_log = logging.getLogger(__name__)

MIN_PROBABILITY: float = 0.0
MAX_PROBABILITY: float = 1.0
DEFAULT_PRECISION: int = 10


def _validate_anchor_points(
    x0: float, y0: float, x1: float, y1: float
) -> None:
    """Ensure anchor points define a valid, non-degenerate segment."""
    if x1 == x0:
        raise ValueError("degenerate segment: x0 and x1 must differ")
    if not (MIN_PROBABILITY <= y0 <= MAX_PROBABILITY):
        raise ValueError(f"y0={y0} outside probability range [{MIN_PROBABILITY}, {MAX_PROBABILITY}]")
    if not (MIN_PROBABILITY <= y1 <= MAX_PROBABILITY):
        raise ValueError(f"y1={y1} outside probability range [{MIN_PROBABILITY}, {MAX_PROBABILITY}]")


def _round_probability(value: float, precision: int = DEFAULT_PRECISION) -> float:
    """Round a probability to avoid floating-point representation noise."""
    return round(value, precision)


def probability_curve(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = True,
) -> float:
    """Linear estimate for probability between two calibration anchor points.

    Performs linear interpolation on the segment defined by (x0, y0) and
    (x1, y1) and evaluates at feature value *x*.  When *clamp* is True the
    result is restricted to lie within [min(y0,y1), max(y0,y1)].

    Args:
        x0: Feature value at the first anchor point.
        y0: Probability at the first anchor point (in [0, 1]).
        x1: Feature value at the second anchor point.
        y1: Probability at the second anchor point (in [0, 1]).
        x: Feature value to evaluate.
        clamp: If True, clamp the output to the anchor-point range.

    Returns:
        Interpolated (and optionally clamped) probability estimate.

    Raises:
        ValueError: If x0 == x1 (degenerate segment) or if anchor
            probabilities fall outside [0, 1].
    """
    _validate_anchor_points(x0, y0, x1, y1)

    t = (x - x0) / (x1 - x0)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("probability_curve: x=%s, t=%.4f, y=%.6f", x, t, y)
    return _round_probability(y)
