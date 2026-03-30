from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Temperature interpolation along sensor line segments.

Used in industrial process monitoring to estimate temperatures at
arbitrary positions between two calibrated sensor readings on a
linear thermal gradient.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 0.0
TEMP_PRECISION_DIGITS = 6


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval."""
    if x1 == x0:
        raise ValueError("zero length")


def _round_temperature(value: float) -> float:
    """Round to the configured precision for consistent output."""
    return round(value, TEMP_PRECISION_DIGITS)


def estimate_temperature(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute temperature along a line segment via linear interpolation.

    Given two sensor positions (x0, x1) with corresponding temperature
    readings (y0, y1), estimates the temperature at an arbitrary
    position x using linear interpolation.

    Args:
        x0: Position of the first sensor.
        y0: Temperature reading at x0.
        x1: Position of the second sensor.
        y1: Temperature reading at x1.
        x: Query position at which to estimate temperature.
        clamp: If True, restrict the result to the range [y0, y1]
            by clamping the interpolation parameter t to [0, 1].

    Returns:
        Estimated temperature at position x, rounded to
        TEMP_PRECISION_DIGITS decimal places.

    Raises:
        ValueError: If x0 == x1 (zero-length segment).
    """
    _validate_segment(x0, x1)

    segment_length = x1 - x0
    t = (x - x0) / (x1 - x0)
    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    _log.debug("Interpolated temp at x=%.4f: t=%.4f, y=%.4f", x, t, y)
    return _round_temperature(y)
