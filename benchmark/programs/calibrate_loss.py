from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Calibration utilities for piecewise-linear loss interpolation.

Used in training pipelines to estimate intermediate loss values between
checkpointed evaluation points, enabling early stopping decisions and
learning-rate schedule adjustments without full evaluation passes.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
SEGMENT_TOLERANCE = 1e-12
MIN_PARAMETER_T = 0.0
MAX_PARAMETER_T = 1.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the interpolation segment is non-degenerate."""
    if abs(x1 - x0) < SEGMENT_TOLERANCE:
        raise ValueError("degenerate segment")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalized interpolation parameter t in [0, 1] range."""
    return (x - x0) / (x1 - x0)


def calibrate_loss(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linear estimate for loss between two evaluation checkpoints.

    Performs linear interpolation (and optional clamping) to estimate
    the loss value at an arbitrary point between two known evaluations.

    Args:
        x0: The x-coordinate of the first evaluation checkpoint.
        y0: The loss value at the first checkpoint.
        x1: The x-coordinate of the second evaluation checkpoint.
        y1: The loss value at the second checkpoint.
        x: The x-coordinate at which to estimate loss.
        clamp: If True, restrict the output to lie within the segment.

    Returns:
        The estimated loss value at position x.

    Raises:
        ValueError: If x0 and x1 are effectively identical (degenerate segment).
    """
    _validate_segment(x0, x1)

    t = _compute_parameter(x, x0, x1)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("calibrate_loss: t=%.4f, y=%.6f, clamp=%s", t, y, clamp)
    return y
