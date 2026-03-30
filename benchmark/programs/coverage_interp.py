from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

"""
Coverage interpolation utilities for signal-processing pipelines.

Provides linear interpolation of coverage metrics between two known
data points, with optional clamping to the segment domain.
"""

DEFAULT_CLAMP = True
SEGMENT_TOLERANCE = 1e-12
MIN_COVERAGE = 0.0
MAX_COVERAGE = 1.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints define a non-degenerate interval."""
    if abs(x1 - x0) < SEGMENT_TOLERANCE:
        raise ValueError("degenerate segment")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the normalized interpolation parameter t in [0, 1] domain."""
    return (x - x0) / (x1 - x0)


def coverage_interp(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linear estimate for coverage between two reference points.

    Performs linear interpolation of a coverage value at position ``x``
    given two known coverage observations ``(x0, y0)`` and ``(x1, y1)``.

    Args:
        x0: Horizontal coordinate of the first reference point.
        y0: Coverage value at the first reference point.
        x1: Horizontal coordinate of the second reference point.
        y1: Coverage value at the second reference point.
        x:  Query position at which to estimate coverage.
        clamp: If ``True``, restrict the result to the segment range
               ``[min(y0,y1), max(y0,y1)]`` so extrapolation is avoided.

    Returns:
        Estimated coverage at position ``x``.

    Raises:
        ValueError: If ``x0`` and ``x1`` are effectively equal.
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

    _log.debug("coverage_interp: t=%.4f, y=%.6f, clamp=%s", t, y, clamp)
    return y
