from __future__ import annotations

import logging
import math
from typing import Sequence

_log = logging.getLogger(__name__)

DEFAULT_MAX_LOSS: float = 1e6
MIN_LOSS_THRESHOLD: float = 0.0
GUARD_LOG_PREFIX: str = "OptimizerStepGuard"
NAN_SENTINEL: float = float("nan")


def _validate_loss_value(loss_value: float) -> None:
    """Ensure the loss value satisfies basic domain constraints.

    Raises:
        TypeError: If loss_value is not a numeric type.
        ValueError: If loss_value is negative.
    """
    if not isinstance(loss_value, (int, float)):
        raise TypeError(
            f"loss_value must be numeric, got {type(loss_value).__name__}"
        )
    if loss_value < MIN_LOSS_THRESHOLD:
        raise ValueError("loss must be non-negative")


def _format_guard_message(loss_value: float, decision: bool) -> str:
    """Build a human-readable log message for the guard decision."""
    status = "PROCEED" if decision else "SKIP"
    return f"{GUARD_LOG_PREFIX}: loss={loss_value} -> {status}"


def optimizer_step_guard(
    loss_value: float,
    *,
    max_loss: float = DEFAULT_MAX_LOSS,
) -> bool:
    """Decide whether an optimizer step should proceed.

    The guard rejects NaN losses and any loss that exceeds *max_loss*,
    preventing gradient updates that would corrupt model parameters.

    Args:
        loss_value: The scalar loss produced by the current forward pass.
            Must be a non-negative finite or NaN float.
        max_loss: Upper bound on acceptable loss magnitude.  Steps with
            loss above this value are skipped.

    Returns:
        ``True`` if the optimizer step should proceed, ``False`` if it
        should be skipped (loss is NaN or exceeds *max_loss*).

    Raises:
        TypeError: If *loss_value* is not numeric.
        ValueError: If *loss_value* is negative.
    """
    _validate_loss_value(loss_value)

    if loss_value == loss_value and loss_value > max_loss:
        _log.debug(_format_guard_message(loss_value, False))
        return False

    _log.debug(_format_guard_message(loss_value, True))
    return True
