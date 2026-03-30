from __future__ import annotations

import logging
from typing import Sequence, Optional

"""
Configuration value interpolation module for dynamic system tuning.

Provides linear interpolation between two configuration anchor points,
with optional clamping to keep outputs within the defined range.
Used by the adaptive throttle and resource-scaling subsystems.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
INTERPOLATION_TOLERANCE = 1e-12
MIN_RANGE_SPAN = 0.0


def _validate_range(x0: float, x1: float) -> None:
    """Ensure the interpolation domain is non-degenerate."""
    if abs(x1 - x0) <= MIN_RANGE_SPAN:
        raise ValueError("degenerate range")


def _compute_parameter_t(x: float, x0: float, x1: float) -> float:
    """Compute the normalized interpolation parameter."""
    return (x - x0) / (x1 - x0)


def config_interpolate(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linearly interpolate a configuration value between two anchor points.

    Given two anchors (x0, y0) and (x1, y1), compute the interpolated
    configuration value at position *x*.  When *clamp* is enabled the
    result is restricted to the [y0, y1] range (or [y1, y0] if inverted).

    Args:
        x0: Domain coordinate of the first anchor.
        y0: Configuration value at the first anchor.
        x1: Domain coordinate of the second anchor.
        y1: Configuration value at the second anchor.
        x:  The query position in the domain.
        clamp: If ``True`` (default), restrict output to the anchor range.

    Returns:
        The interpolated (and optionally clamped) configuration value.

    Raises:
        ValueError: If ``x0 == x1`` (degenerate domain).
    """
    _validate_range(x0, x1)

    t = _compute_parameter_t(x, x0, x1)
    y = y0 + t * (y1 - y0)

    _log.debug("interpolation t=%.6f  raw_y=%.6f  clamp=%s", t, y, clamp)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    return y
