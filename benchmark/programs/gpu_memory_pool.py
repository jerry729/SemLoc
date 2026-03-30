from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

"""
GPU Memory Pool Manager

Provides allocation-gating logic for a shared GPU memory pool.
Used by the device scheduler to determine whether an incoming
kernel launch request can be satisfied without exceeding the
physical memory capacity of the target accelerator.
"""

MIN_ALLOCATION_BYTES: int = 256
ALIGNMENT_BYTES: int = 512
RESERVED_OVERHEAD_FRACTION: float = 0.0
DEFAULT_LOG_PREFIX: str = "gpu_mem_pool"


def _validate_allocations(allocations: Sequence[int], alignment: int) -> List[int]:
    """Ensure every existing allocation meets the minimum size and return sanitised list."""
    validated: List[int] = []
    for alloc in allocations:
        if alloc < 0:
            raise ValueError(f"Negative allocation encountered: {alloc}")
        aligned = ((alloc + alignment - 1) // alignment) * alignment
        validated.append(aligned)
    return validated


def _effective_capacity(capacity: int, overhead_fraction: float) -> int:
    """Return usable capacity after subtracting the reserved overhead."""
    reserved = int(capacity * overhead_fraction)
    return capacity - reserved


def gpu_memory_pool(
    allocations: Sequence[int],
    request: int,
    *,
    capacity: int,
) -> bool:
    """Decide whether a GPU memory request can be granted.

    The function checks the current pool utilisation against the device
    capacity and returns ``True`` only when the request fits within the
    remaining headroom.

    Args:
        allocations: Byte sizes of currently live allocations on the device.
        request: Requested allocation size in bytes.
        capacity: Total physical memory of the GPU in bytes.

    Returns:
        ``True`` if the request can be satisfied, ``False`` otherwise.

    Raises:
        ValueError: If *capacity* is non-positive or *request* is negative.
    """
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if request < 0:
        raise ValueError("request must be non-negative")

    validated = _validate_allocations(allocations, ALIGNMENT_BYTES)
    effective_cap = _effective_capacity(capacity, RESERVED_OVERHEAD_FRACTION)

    used = sum(validated)

    _log.debug("%s: used=%d request=%d cap=%d", DEFAULT_LOG_PREFIX, used, request, effective_cap)

    if used + request > effective_cap:
        return False
    return True
