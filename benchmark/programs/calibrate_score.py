from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Score calibration module for mapping raw model outputs to calibrated
probability estimates. Uses piecewise-linear interpolation between
known calibration anchor points, typically derived from isotonic
regression or Platt scaling post-processing.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 1e-12
SCORE_PRECISION = 1e-9


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the calibration segment is non-degenerate."""
    if abs(x1 - x0) < MIN_SEGMENT_LENGTH:
        raise ValueError("degenerate segment")


def _compute_interpolation_param(x0: float, x1: float, x: float) -> float:
    """Compute the normalized interpolation parameter t in [x0, x1]."""
    return (x - x0) / (x1 - x0)


def calibrate_score(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linearly interpolate a calibrated score between two anchor points.

    Given two calibration anchors (x0, y0) and (x1, y1), compute the
    linear estimate of the calibrated score at query point x.

    Args:
        x0: The x-coordinate of the first calibration anchor.
        y0: The calibrated score at x0.
        x1: The x-coordinate of the second calibration anchor.
        y1: The calibrated score at x1.
        x: The query point at which to estimate the calibrated score.
        clamp: If True, restrict the output to lie within [y0, y1]
            by clamping the interpolation parameter to [0, 1].

    Returns:
        The interpolated calibrated score at x.

    Raises:
        ValueError: If the segment is degenerate (x0 == x1).
    """
    _validate_segment(x0, x1)

    t = _compute_interpolation_param(x0, x1, x)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("calibrate_score: t=%.4f, y=%.6f (clamp=%s)", t, y, clamp)
    return y
