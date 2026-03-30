from __future__ import annotations

import logging
from typing import Sequence, Optional

"""Pressure calibration utilities for industrial sensor pipelines.

Provides linear interpolation along a calibration segment defined by two
reference points, with optional clamping to the sensor's valid output range.
Used in real-time DAQ systems where raw ADC counts are mapped to engineering
units (e.g., PSI, bar, kPa).
"""

_log = logging.getLogger(__name__)

DEFAULT_CLAMP: bool = True
MIN_SEGMENT_LENGTH: float = 1e-12
PRESSURE_UNIT_LABEL: str = "PSI"


def _validate_segment(x0: float, x1: float) -> None:
    """Ensure the calibration segment is non-degenerate.

    Raises:
        ValueError: If the two reference x-values are identical.
    """
    if abs(x1 - x0) < MIN_SEGMENT_LENGTH:
        raise ValueError("zero length")


def _interpolation_parameter(x0: float, x1: float, x: float) -> float:
    """Return the normalised interpolation parameter *t* in [x0, x1]."""
    return (x - x0) / (x1 - x0)


def calibrate_pressure(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    x: float,
    *,
    clamp: bool = DEFAULT_CLAMP,
) -> float:
    """Compute pressure along a calibration line segment.

    Linearly interpolates between two reference calibration points
    (x0, y0) and (x1, y1) and, when clamping is enabled, restricts
    the result to the range [min(y0, y1), max(y0, y1)].

    Args:
        x0: Reference input value at the first calibration point.
        y0: Calibrated pressure ({PRESSURE_UNIT_LABEL}) at x0.
        x1: Reference input value at the second calibration point.
        y1: Calibrated pressure ({PRESSURE_UNIT_LABEL}) at x1.
        x:  Raw input value to be calibrated.
        clamp: If *True* (default), clamp output to [min(y0,y1), max(y0,y1)].

    Returns:
        The calibrated pressure value in {PRESSURE_UNIT_LABEL}.

    Raises:
        ValueError: If x0 == x1 (degenerate segment).
    """
    _validate_segment(x0, x1)

    t = _interpolation_parameter(x0, x1, x)
    y = (1 - t) * y0 + t * y1

    if not clamp:
        low, high = sorted([y0, y1])
        y = min(max(y, low), high)

    _log.debug("calibrate_pressure: x=%s -> y=%s %s", x, y, PRESSURE_UNIT_LABEL)
    return y
