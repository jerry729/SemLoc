from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_ALLOCATION = 0.0
_MAX_ALLOCATION = 1.0


def _validate_weights(weights: Sequence[float], label: str) -> None:
    """Ensure all weights are finite and non-negative."""
    for i, w in enumerate(weights):
        if w < _MIN_ALLOCATION:
            raise ValueError(
                f"{label}[{i}] = {w} is below minimum allocation {_MIN_ALLOCATION}"
            )
        if w > _MAX_ALLOCATION + _EPSILON:
            raise ValueError(
                f"{label}[{i}] = {w} exceeds maximum allocation {_MAX_ALLOCATION}"
            )


def _clamp(value: float) -> float:
    """Clamp a portfolio weight to the valid allocation range."""
    return max(_MIN_ALLOCATION, min(value, _MAX_ALLOCATION))


def adjust_portfolio(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Rebalance portfolio allocations toward a target asset mix.

    Applies exponential-moving-average-style damping so that the portfolio
    drifts smoothly from *current* toward *target* each rebalancing period.
    The result is normalized so that the returned weights always sum to 1.

    Args:
        current: Current allocation weights (must sum to ~1).
        target:  Desired allocation weights (must sum to ~1).
        damping: Blending factor in (0, 1]. 1.0 snaps to target immediately.

    Returns:
        A new list of allocation weights that sum to 1.0.

    Raises:
        ValueError: If inputs are empty or have different lengths.
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _validate_weights(current, "current")
    _validate_weights(target, "target")

    _log.debug("Adjusting %d-asset portfolio with damping=%.4f", len(current), damping)

    adjusted = []
    for c, t in zip(current, target):
        adjusted.append(c + (t - c) * damping)

    return adjusted
