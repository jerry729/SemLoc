from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

"""
Sensor quality calibration module.

Provides linear interpolation utilities for mapping raw sensor readings
to calibrated quality scores, commonly used in industrial process control
and environmental monitoring pipelines.
"""

DEFAULT_CLAMP = True
SEGMENT_TOLERANCE = 1e-12
MIN_QUALITY = 0.0
MAX_QUALITY = 100.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the interpolation segment is non-degenerate."""
    if abs(x1 - x0) < SEGMENT_TOLERANCE:
        raise ValueError("degenerate segment: x0 and x1 are effectively equal")


def _normalize_quality(y: float) -> float:
    """Clip a quality value to the globally valid quality range."""
    return max(MIN_QUALITY, min(MAX_QUALITY, y))


def calibrate_quality(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linearly interpolate a quality score between two calibration points.

    Given a calibration segment defined by ``(x0, y0)`` and ``(x1, y1)``,
    compute the quality value at position ``x`` via linear interpolation.
    When *clamp* is enabled the result is restricted to the range spanned
    by the two calibration endpoints.

    Args:
        x0: Independent-variable value at the first calibration point.
        y0: Quality score at the first calibration point.
        x1: Independent-variable value at the second calibration point.
        y1: Quality score at the second calibration point.
        x: The query position for which to estimate quality.
        clamp: If ``True``, restrict the output to the segment bounds.

    Returns:
        The estimated quality score at position *x*.

    Raises:
        ValueError: If the segment is degenerate (x0 == x1).
    """
    _validate_segment(x0, x1)

    t = (x - x0) / (x1 - x0)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("calibrate_quality: x=%s, t=%.4f, y=%.4f", x, t, y)
    return _normalize_quality(y)
