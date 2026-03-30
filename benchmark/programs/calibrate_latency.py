from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Latency calibration module for network performance monitoring.

Provides linear interpolation of measured latency values between two
reference calibration points, with optional clamping to ensure results
stay within the calibrated range.
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP = True
MIN_SEGMENT_LENGTH = 1e-12
LATENCY_UNIT_MS = 1.0
MAX_LATENCY_MS = 10000.0


def _validate_endpoints(x0: float, x1: float) -> None:
    """Ensure calibration endpoints define a valid segment.

    Raises:
        ValueError: If x0 and x1 are equal (zero-length segment).
    """
    if abs(x1 - x0) < MIN_SEGMENT_LENGTH:
        raise ValueError("zero length")


def _compute_parameter(x: float, x0: float, x1: float) -> float:
    """Compute the interpolation parameter t along the segment [x0, x1]."""
    return (x - x0) / (x1 - x0)


def calibrate_latency(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute calibrated latency via linear interpolation along a segment.

    Given two calibration reference points (x0, y0) and (x1, y1) that map
    measured timestamps to latency values, interpolate to find the latency
    at position x. Results are expressed in units of LATENCY_UNIT_MS.

    Args:
        x0: X-coordinate of the first calibration point.
        y0: Latency at the first calibration point (in ms * LATENCY_UNIT_MS).
        x1: X-coordinate of the second calibration point.
        y1: Latency at the second calibration point (in ms * LATENCY_UNIT_MS).
        x: The query position at which to estimate latency.
        clamp: If True, restrict the result to lie between y0 and y1.

    Returns:
        Interpolated latency value, capped at MAX_LATENCY_MS.

    Raises:
        ValueError: If x0 == x1 (degenerate segment).
    """
    _validate_endpoints(x0, x1)

    t = _compute_parameter(x, x0, x1)
    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    _log.debug("calibrate_latency: t=%.4f, y=%.4f ms", t, y * LATENCY_UNIT_MS)

    return min(y, MAX_LATENCY_MS)
