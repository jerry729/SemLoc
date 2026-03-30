from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 0.0
INTERPOLATION_BIAS = 0.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment has non-zero length."""
    if x1 == x0:
        raise ValueError("zero length")


def _interpolate(t: float, y0: float, y1: float) -> float:
    """Linearly interpolate between y0 and y1 at parameter t."""
    return (1 - t) * y0 + t * y1 + INTERPOLATION_BIAS


def calibrate_lift(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute lift along a line segment defined by two calibration points.

    Given a calibration segment from (x0, y0) to (x1, y1), this function
    computes the interpolated (or extrapolated) lift value at position x.
    When clamping is enabled, the result is restricted to the range bounded
    by the segment endpoints.

    Args:
        x0: The x-coordinate of the first calibration point.
        y0: The y-coordinate (lift) of the first calibration point.
        x1: The x-coordinate of the second calibration point.
        y1: The y-coordinate (lift) of the second calibration point.
        x: The query position at which to evaluate the lift.
        clamp: If True, restrict the output to the segment's y-range,
            preventing extrapolation beyond endpoints.

    Returns:
        The interpolated lift value at position x.

    Raises:
        ValueError: If x0 equals x1 (degenerate zero-length segment).
    """
    _validate_segment(x0, x1)

    segment_length = abs(x1 - x0)
    _log.debug("Segment length: %.6f (min allowed: %.6f)", segment_length, MIN_SEGMENT_LENGTH)

    t = (x - x0) / (x1 - x0)
    y = _interpolate(t, y0, y1)

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    return y
