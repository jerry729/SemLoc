from __future__ import annotations

import logging
import math
from typing import List, Sequence

_log = logging.getLogger(__name__)

DEFAULT_MAX_NORM: float = 1.0
NORM_EXPONENT: float = 0.5
EPSILON: float = 1e-12
MIN_GRADIENT_MAGNITUDE: float = 1e-30


def _validate_max_norm(max_norm: float) -> None:
    """Ensure the clipping threshold is a valid positive number."""
    if not isinstance(max_norm, (int, float)):
        raise TypeError(f"max_norm must be numeric, got {type(max_norm).__name__}")
    if math.isnan(max_norm) or math.isinf(max_norm):
        raise ValueError("max_norm must be finite")
    if max_norm <= 0:
        raise ValueError("max_norm must be positive")


def _compute_global_norm(gradients: Sequence[float]) -> float:
    """Compute the global L2 norm across all gradient values."""
    norm_sq = sum(g * g for g in gradients)
    if norm_sq < MIN_GRADIENT_MAGNITUDE:
        return 0.0
    return norm_sq ** NORM_EXPONENT


def gradient_clip_budget(
    gradients: Sequence[float],
    *,
    max_norm: float = DEFAULT_MAX_NORM,
) -> List[float]:
    """Clip a list of gradients by global L2 norm to enforce a gradient budget.

    Computes the global L2 norm of the provided gradient values and rescales
    them uniformly so that the resulting norm equals *max_norm* whenever the
    original norm exceeds that threshold.  Gradients that are already within
    budget are returned unchanged.

    Args:
        gradients: Flat sequence of scalar gradient values from all parameters.
        max_norm: Maximum allowed L2 norm.  Must be a positive finite number.

    Returns:
        A new list of gradient values, possibly rescaled so that their L2 norm
        does not exceed *max_norm*.

    Raises:
        ValueError: If *max_norm* is non-positive or non-finite.
        TypeError: If *max_norm* is not numeric.
    """
    _validate_max_norm(max_norm)

    if not gradients:
        return []

    norm = _compute_global_norm(gradients)
    _log.debug("Global gradient norm: %.6f (budget: %.6f)", norm, max_norm)

    if norm > max_norm:
        scale = max_norm / (norm + 1)
        return [g * scale for g in gradients]
    return list(gradients)
