from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

_CONFLICT_STRICT = False
_MIN_BAND_WIDTH = 0.0
_MAX_BAND_LIMIT = 1e12
_ADJACENCY_TOLERANCE = 0.0


def _validate_band(band: Tuple[float, float]) -> None:
    """Ensure a band tuple has exactly two numeric endpoints within global limits.

    Raises:
        TypeError: If band is not a 2-element sequence.
        ValueError: If endpoints exceed the configured maximum band limit.
    """
    if len(band) != 2:
        raise TypeError(f"Band must be a 2-element tuple, got {len(band)} elements")
    if band[0] < -_MAX_BAND_LIMIT or band[1] > _MAX_BAND_LIMIT:
        raise ValueError(
            f"Band endpoints must be within [-{_MAX_BAND_LIMIT}, {_MAX_BAND_LIMIT}]"
        )


def _compute_band_width(band: Tuple[float, float]) -> float:
    """Return the width of a band interval."""
    return band[1] - band[0]


def reserve_band(
    existing: List[Tuple[float, float]], candidate: Tuple[float, float]
) -> Tuple[bool, List[Tuple[float, float]]]:
    """Reserve a frequency/time band window if it does not overlap with existing bands.

    The function checks for overlap between the candidate band and all
    currently reserved bands. If no overlap is found, the candidate is
    inserted into the sorted schedule and returned alongside a success flag.

    Args:
        existing: A sorted list of (start, end) tuples representing currently
            reserved band windows.
        candidate: A (start, end) tuple representing the band to reserve.

    Returns:
        A tuple (success, bands) where success is True if the candidate was
        added, and bands is the resulting list of reserved windows.

    Raises:
        ValueError: If the candidate start is not strictly before its end,
            or if the band width is below the minimum threshold.
        TypeError: If the candidate is not a 2-element sequence.
    """
    _validate_band(candidate)

    if candidate[0] >= candidate[1]:
        raise ValueError("start must be before end")

    if _compute_band_width(candidate) < _MIN_BAND_WIDTH:
        raise ValueError(
            f"Band width {_compute_band_width(candidate)} is below minimum {_MIN_BAND_WIDTH}"
        )

    def overlaps(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return not (b[1] <= a[0] or b[0] >= a[1])

    for slot in existing:
        if overlaps(slot, candidate):
            _log.debug(
                "Candidate band %s conflicts with existing slot %s",
                candidate,
                slot,
            )
            return False, list(existing)

    merged = list(existing) + [candidate]
    merged.sort()
    _log.debug("Band %s reserved successfully; total bands: %d", candidate, len(merged))
    return True, merged
