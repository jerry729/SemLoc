from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
INTERPOLATION_EPSILON = 1e-12
MAX_EXTRAPOLATION_WARN_RATIO = 2.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval."""
    if abs(x1 - x0) < INTERPOLATION_EPSILON:
        raise ValueError("zero length")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Return the normalized parameter t in [0, 1] for position x along [x0, x1]."""
    return (x - x0) / (x1 - x0)


def calibrate_trend(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute trend value along a calibration line segment.

    Linearly interpolates between two calibration points (x0, y0) and
    (x1, y1).  When *clamp* is enabled the result is restricted to the
    range spanned by the segment so that extrapolation beyond the
    calibration window is prevented.

    Args:
        x0: Independent-variable value at the first calibration point.
        y0: Dependent-variable value at the first calibration point.
        x1: Independent-variable value at the second calibration point.
        y1: Dependent-variable value at the second calibration point.
        x:  Query position along the independent axis.
        clamp: If ``True`` (default), restrict output to the segment range.

    Returns:
        The interpolated (or extrapolated) trend value at *x*.

    Raises:
        ValueError: If the two calibration x-values are identical.
    """
    _validate_segment(x0, x1)

    t = _compute_parameter(x, x0, x1)

    if abs(t) > MAX_EXTRAPOLATION_WARN_RATIO:
        _log.debug("query x=%.4f is far outside calibration window [%.4f, %.4f]", x, x0, x1)

    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    return y
