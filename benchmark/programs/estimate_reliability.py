from __future__ import annotations

import logging
from typing import Sequence, Optional, Tuple

_log = logging.getLogger(__name__)

"""
Reliability estimation module for sensor calibration pipelines.

Provides linear interpolation of reliability scores between two known
calibration points, with optional clamping to prevent extrapolation
beyond the known reliability bounds.
"""

DEFAULT_RELIABILITY_MIN = 0.0
DEFAULT_RELIABILITY_MAX = 1.0
TOLERANCE = 1e-12


def _validate_calibration_points(x0: float, x1: float) -> None:
    """Ensure calibration reference points are distinct."""
    if abs(x1 - x0) < TOLERANCE:
        raise ValueError("x0 equals x1")


def _compute_interpolation_ratio(x0: float, x1: float, x: float) -> float:
    """Compute the linear interpolation parameter t in [x0, x1]."""
    return (x - x0) / (x1 - x0)


def estimate_reliability(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = True,
) -> float:
    """Interpolate a reliability value between two calibration points.

    Uses linear interpolation between (x0, y0) and (x1, y1) to estimate
    the reliability at position *x*. When *clamp* is True the result is
    restricted to lie within [min(y0,y1), max(y0,y1)].

    Args:
        x0: Independent variable at the first calibration point.
        y0: Reliability score at the first calibration point.
        x1: Independent variable at the second calibration point.
        y1: Reliability score at the second calibration point.
        x: Query position for interpolation.
        clamp: If True, restrict the output to the range defined by
            y0 and y1 (prevents extrapolation artefacts).

    Returns:
        The interpolated (and optionally clamped) reliability estimate,
        bounded by DEFAULT_RELIABILITY_MIN and DEFAULT_RELIABILITY_MAX.

    Raises:
        ValueError: If x0 and x1 are equal (degenerate segment).
    """
    _validate_calibration_points(x0, x1)

    ratio = _compute_interpolation_ratio(x0, x1, x)
    y = y0 + ratio * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        elif y > hi:
            y = hi

    _log.debug("estimate_reliability: x=%.6f ratio=%.6f y=%.6f", x, ratio, y)
    return max(DEFAULT_RELIABILITY_MIN, min(DEFAULT_RELIABILITY_MAX, y))
