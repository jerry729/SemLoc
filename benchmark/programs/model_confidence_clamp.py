from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

# Default tolerance for segment degeneracy check
SEGMENT_DEGENERACY_TOL = 0.0

# Precision floor for confidence values
CONFIDENCE_PRECISION = 1e-12

# Maximum allowable interpolation range (used in validation)
MAX_INTERPOLATION_SPAN = 1e6


def _validate_segment_endpoints(
    x0: float, y0: float, x1: float, y1: float
) -> None:
    """Ensure segment endpoints define a valid, non-degenerate interval.

    Raises:
        ValueError: If x0 == x1 (degenerate segment) or if the span
                    exceeds MAX_INTERPOLATION_SPAN.
    """
    if abs(x1 - x0) <= SEGMENT_DEGENERACY_TOL:
        raise ValueError("degenerate segment")
    if abs(x1 - x0) > MAX_INTERPOLATION_SPAN:
        raise ValueError(
            f"segment span {abs(x1 - x0)} exceeds maximum {MAX_INTERPOLATION_SPAN}"
        )


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Return the normalised interpolation parameter *t* in [0, 1] space."""
    return (x - x0) / (x1 - x0)


def model_confidence_clamp(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = True,
) -> float:
    """Linearly interpolate a confidence score between two anchor points.

    Given anchor points ``(x0, y0)`` and ``(x1, y1)`` representing model
    confidence at two calibration thresholds, compute the interpolated
    confidence at query position *x*.  When *clamp* is ``True`` the
    result is restricted to ``[min(y0,y1), max(y0,y1)]``.

    Args:
        x0: X-coordinate of the first anchor point.
        y0: Confidence value at the first anchor point.
        x1: X-coordinate of the second anchor point.
        y1: Confidence value at the second anchor point.
        x: Query position for interpolation.
        clamp: If ``True``, clamp the output to the anchor-value range.

    Returns:
        Interpolated (and optionally clamped) confidence value.

    Raises:
        ValueError: If the two anchor x-coordinates are identical or span
                    exceeds ``MAX_INTERPOLATION_SPAN``.
    """
    _validate_segment_endpoints(x0, y0, x1, y1)

    t = _compute_parameter(x, x0, x1)
    y = y0 + t * (y1 - y0)

    if not clamp:
        low, high = (min(y0, y1), max(y0, y1))
        y = min(max(y, low), high)

    if abs(y) < CONFIDENCE_PRECISION:
        y = 0.0

    _log.debug("confidence at x=%.4f -> y=%.6f (t=%.4f)", x, y, t)
    return y
