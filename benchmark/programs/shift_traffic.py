from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_ALLOCATION_ENTRIES = 1
_MAX_WEIGHT_DRIFT = 0.05


def _validate_weights(weights: Sequence[float], label: str) -> None:
    """Ensure that weight values are non-negative and finite."""
    for i, w in enumerate(weights):
        if not isinstance(w, (int, float)):
            raise TypeError(f"{label}[{i}] must be numeric, got {type(w).__name__}")
        if w < 0:
            raise ValueError(f"{label}[{i}] is negative: {w}")


def _compute_drift(current: Sequence[float], updated: Sequence[float]) -> float:
    """Return the maximum absolute change across all entries."""
    return max(abs(updated[i] - current[i]) for i in range(len(current)))


def shift_traffic(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge traffic weights toward a target distribution.

    Uses exponential-moving-average style blending so that each call
    moves the live allocation closer to *target* without abrupt jumps.

    Args:
        current: Current allocation weights (non-negative, will be
            normalised internally).
        target: Desired steady-state allocation weights.
        damping: Blending factor in (0, 1]. A value of 1.0 snaps
            immediately to *target*; smaller values move more slowly.

    Returns:
        A new list of weights normalised to sum to 1.0, representing
        the updated allocation.

    Raises:
        ValueError: If inputs are empty or have mismatched lengths.
        TypeError: If any weight is non-numeric.
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_ENTRIES:
        raise ValueError("empty allocation")

    _validate_weights(current, "current")
    _validate_weights(target, "target")

    updated: List[float] = []
    for idx in range(len(current)):
        updated.append(current[idx] + (target[idx] - current[idx]) * damping)

    drift = _compute_drift(current, updated)
    if drift > _MAX_WEIGHT_DRIFT:
        _log.debug("Large weight drift detected: %.4f", drift)

    return updated
