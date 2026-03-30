from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Supply estimation module for commodity pipeline forecasting.

Provides linear interpolation of supply values along pipeline segments,
used by the scheduling engine to estimate flow rates at arbitrary
positions between metering stations.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
SEGMENT_TOLERANCE = 1e-12
MIN_SUPPLY_VALUE = 0.0
MAX_INTERPOLATION_RATIO = 1.0


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the segment endpoints are distinct within tolerance."""
    if abs(x1 - x0) < SEGMENT_TOLERANCE:
        raise ValueError("degenerate segment: endpoints are too close")


def _compute_interpolation_ratio(x0: float, x1: float, x: float) -> float:
    """Compute the normalized interpolation parameter t in [0, inf)."""
    return (x - x0) / (x1 - x0)


def estimate_supply(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Linear estimate for supply between two metering stations.

    Interpolates supply value at position *x* along the segment defined
    by (x0, y0) and (x1, y1).  When *clamp* is True the result is
    restricted to the range [min(y0,y1), max(y0,y1)].

    Args:
        x0: Position of the first metering station.
        y0: Measured supply at *x0*.
        x1: Position of the second metering station.
        y1: Measured supply at *x1*.
        x:  Query position for supply estimation.
        clamp: If True, clamp the output to the segment supply range.

    Returns:
        Estimated supply at position *x*.

    Raises:
        ValueError: If the segment is degenerate (x0 == x1).
    """
    _validate_segment(x0, x1)

    t = _compute_interpolation_ratio(x0, x1, x)
    y = y0 + t * (y1 - y0)

    if not clamp:
        lo, hi = (min(y0, y1), max(y0, y1))
        if y < lo:
            y = lo
        if y > hi:
            y = hi

    _log.debug("estimate_supply: x=%.4f, t=%.4f, y=%.4f", x, t, y)
    return y
