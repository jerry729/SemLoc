from __future__ import annotations

import logging
from typing import Sequence, Optional

_log = logging.getLogger(__name__)

# Minimum learning rate floor to avoid numerical instability
MIN_LR_FLOOR: float = 0.0

# Default warmup horizon used across training pipelines
DEFAULT_WARMUP_STEPS: int = 100

# Default base learning rate matching optimizer defaults
DEFAULT_BASE_LR: float = 1e-3


def _validate_positive_int(value: int, name: str) -> None:
    """Ensure a parameter is a positive integer."""
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_non_negative(value: int, name: str) -> None:
    """Ensure a parameter is non-negative."""
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def lr_warmup_schedule(
    step: int,
    *,
    base_lr: float = DEFAULT_BASE_LR,
    warmup_steps: int = DEFAULT_WARMUP_STEPS,
) -> float:
    """Compute the learning rate at a given training step using a linear warmup.

    During the warmup phase (step 0 through warmup_steps), the learning rate
    increases linearly from MIN_LR_FLOOR to base_lr. After warmup completes
    the returned rate is clamped at base_lr.

    Args:
        step: Current training step (0-indexed).
        base_lr: Target learning rate after warmup finishes.
        warmup_steps: Number of steps over which the learning rate ramps up.

    Returns:
        The scheduled learning rate for the given step, guaranteed to be
        at least ``MIN_LR_FLOOR``.

    Raises:
        ValueError: If warmup_steps is not positive or step is negative.
    """
    _validate_positive_int(warmup_steps, "warmup_steps")
    _validate_non_negative(step, "step")

    if step >= warmup_steps:
        return base_lr
    lr = base_lr * ((step + 1) / warmup_steps)

    _log.debug("step=%d  lr=%.6e", step, lr)
    return max(lr, MIN_LR_FLOOR)
