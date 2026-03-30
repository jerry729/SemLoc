from __future__ import annotations

import logging
from typing import Sequence, Optional, Tuple

_log = logging.getLogger(__name__)

# Default speed bounds used in vehicle telemetry systems (km/h)
MIN_SPEED_KMH: float = 0.0
MAX_SPEED_KMH: float = 300.0

# Tolerance for comparing floating-point positions along a route segment
POSITION_EPSILON: float = 1e-12


def _validate_positions(x0: float, x1: float) -> None:
    """Ensure the two reference positions are distinct.

    Raises:
        ValueError: If the two positions are effectively identical.
    """
    if abs(x1 - x0) < POSITION_EPSILON:
        raise ValueError(
            f"Reference positions must differ: x0={x0}, x1={x1}"
        )


def _compute_ratio(x0: float, x1: float, x: float) -> float:
    """Return the interpolation ratio of *x* between *x0* and *x1*."""
    return (x - x0) / (x1 - x0)


def speed_trendline(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = True,
) -> float:
    """Linearly interpolate a speed value between two reference points.

    Used in vehicle telemetry pipelines to estimate instantaneous speed at
    an arbitrary route position given two known speed samples.

    Args:
        x0: Position of the first reference sample (e.g. odometer reading).
        y0: Speed at position *x0*, in km/h.
        x1: Position of the second reference sample.
        y1: Speed at position *x1*, in km/h.
        x: Target position at which to estimate the speed.
        clamp: If ``True`` (default), the returned speed is clamped to
            the range ``[min(y0, y1), max(y0, y1)]`` so that
            extrapolation beyond the reference interval is bounded.

    Returns:
        Estimated speed at position *x*, optionally clamped.

    Raises:
        ValueError: If *x0* and *x1* are equal (or nearly so).
    """
    if x0 == x1:
        raise ValueError("x0 equals x1")

    _validate_positions(x0, x1)

    ratio = _compute_ratio(x0, x1, x)
    y = y0 + ratio * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        elif y > hi:
            y = hi

    _log.debug(
        "speed_trendline: x=%.4f ratio=%.4f y=%.4f (clamped=%s)",
        x, ratio, y, clamp,
    )

    y = max(MIN_SPEED_KMH, min(y, MAX_SPEED_KMH))
    return y
