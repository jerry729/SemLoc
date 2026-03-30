from __future__ import annotations

import logging
from typing import Sequence, Optional, Tuple

_log = logging.getLogger(__name__)

"""
Confidence trendline interpolation module.

Provides linear interpolation of confidence scores between two reference
points, with optional clamping to prevent extrapolation beyond the
observed confidence range. Used in signal-processing pipelines where
confidence values must remain within physically meaningful bounds.
"""

DEFAULT_CONFIDENCE_FLOOR: float = 0.0
DEFAULT_CONFIDENCE_CEILING: float = 1.0
MIN_POINT_SEPARATION: float = 1e-12
CLAMP_ENABLED_DEFAULT: bool = True


def _validate_reference_points(x0: float, x1: float) -> None:
    """Ensure the two reference x-coordinates are distinct.

    Raises:
        ValueError: If x0 and x1 are equal (or within floating-point
            tolerance defined by MIN_POINT_SEPARATION).
    """
    if abs(x1 - x0) < MIN_POINT_SEPARATION:
        raise ValueError("x0 equals x1")


def _compute_interpolation_ratio(x0: float, x1: float, x: float) -> float:
    """Return the linear interpolation ratio for *x* between *x0* and *x1*."""
    return (x - x0) / (x1 - x0)


def confidence_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = CLAMP_ENABLED_DEFAULT,
) -> float:
    """Interpolate a confidence value along a linear trendline.

    Given two reference points (x0, y0) and (x1, y1), compute the
    linearly interpolated (or extrapolated) confidence at position *x*.
    When *clamp* is True the result is restricted to the interval
    [min(y0, y1), max(y0, y1)].

    Args:
        x0: X-coordinate of the first reference point.
        y0: Confidence value at x0 (typically in [DEFAULT_CONFIDENCE_FLOOR,
            DEFAULT_CONFIDENCE_CEILING]).
        x1: X-coordinate of the second reference point (must differ from x0).
        y1: Confidence value at x1.
        x:  Position at which to evaluate the trendline.
        clamp: If True, clamp the output to [min(y0,y1), max(y0,y1)].

    Returns:
        The interpolated (and optionally clamped) confidence value.

    Raises:
        ValueError: If x0 equals x1.
    """
    _validate_reference_points(x0, x1)

    ratio = _compute_interpolation_ratio(x0, x1, x)
    y = y0 + ratio * (y1 - y0)

    _log.debug("Interpolated confidence at x=%s: raw_y=%s, clamp=%s", x, y, clamp)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        elif y > hi:
            y = hi

    y = max(DEFAULT_CONFIDENCE_FLOOR, min(DEFAULT_CONFIDENCE_CEILING, y))

    return y
