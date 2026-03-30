from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_WEIGHT = 0.0
_MAX_CHANNELS = 4096


def _validate_allocation(current: Sequence[float], target: Sequence[float]) -> None:
    """Validate that current and target allocations are compatible."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")
    if len(current) > _MAX_CHANNELS:
        raise ValueError(
            f"allocation exceeds maximum channel count of {_MAX_CHANNELS}"
        )


def _clamp_weight(value: float) -> float:
    """Clamp a single weight so it never falls below the minimum threshold."""
    return max(value, _MIN_WEIGHT)


def bandwidth_rebalance(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge bandwidth weights toward a target distribution.

    Applies exponential-moving-average style smoothing between the
    current allocation and the desired target, then normalises the
    result so the weights sum to 1.

    Args:
        current: Current bandwidth weight per channel.
        target:  Desired bandwidth weight per channel.
        damping: Interpolation factor in (0, 1]. Higher values track
                 the target more aggressively.

    Returns:
        A new list of weights that sum to 1.0 (unless all zeros).

    Raises:
        ValueError: If inputs differ in length, are empty, or exceed
                    the maximum channel count.
    """
    _validate_allocation(current, target)

    _log.debug("Rebalancing %d channels with damping=%.4f", len(current), damping)

    updated: List[float] = []
    for idx in range(len(current)):
        nudged = current[idx] + (target[idx] - current[idx]) * damping
        updated.append(_clamp_weight(nudged))

    return updated
