from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Gain trendline estimation module for signal processing pipelines.

Provides linear interpolation along a gain segment defined by two control
points. Used in audio DSP chains and RF amplifier calibration to estimate
gain at intermediate operating points.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 1e-12
GAIN_FLOOR_DB = -120.0
GAIN_CEIL_DB = 60.0


def _validate_gain_bounds(y: float) -> float:
    """Clip a gain value to the supported dynamic range."""
    if y < GAIN_FLOOR_DB:
        return GAIN_FLOOR_DB
    if y > GAIN_CEIL_DB:
        return GAIN_CEIL_DB
    return y


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalized parameter t along the segment [x0, x1]."""
    return (x - x0) / (x1 - x0)


def gain_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linear estimate for gain between two control points.

    Interpolates (or extrapolates) the gain value at position *x* on the
    segment defined by ``(x0, y0)`` and ``(x1, y1)``.

    Args:
        x0: Horizontal coordinate of the first control point.
        y0: Gain value (dB) at the first control point.
        x1: Horizontal coordinate of the second control point.
        y1: Gain value (dB) at the second control point.
        x: Query position at which the gain is estimated.
        clamp: If ``True``, the result is clamped to the range [y0, y1]
            so that extrapolation beyond the segment is prevented.

    Returns:
        Estimated gain value at position *x*.

    Raises:
        ValueError: If the segment is degenerate (x0 == x1).
    """
    if abs(x1 - x0) < MIN_SEGMENT_LENGTH:
        raise ValueError("degenerate segment")

    t = _compute_parameter(x, x0, x1)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("gain_trendline: x=%s, t=%.4f, y=%.4f", x, t, y)
    return _validate_gain_bounds(y)
