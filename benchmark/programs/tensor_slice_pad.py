from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

DEFAULT_PAD_VALUE = 0
MIN_SLICE_LENGTH = 0
MAX_SLICE_LENGTH = 10_000_000


def _validate_range(start: int, end: int) -> None:
    """Ensure the requested slice range is non-negative and well-ordered."""
    if start < 0 or end < start:
        raise ValueError(
            f"invalid range: start={start}, end={end}; "
            f"expected 0 <= start <= end"
        )


def _compute_missing_count(requested_length: int, actual_length: int) -> int:
    """Return how many pad elements are needed to fill the gap."""
    return requested_length - actual_length


def tensor_slice_pad(
    values: List[int],
    start: int,
    end: int,
    *,
    pad: int = DEFAULT_PAD_VALUE,
) -> List[int]:
    """Extract a fixed-width slice from *values*, padding when the requested
    window extends beyond the underlying data.

    This is commonly used in tensor pre-processing pipelines where each
    sample must have a uniform length before being fed into a model.

    Args:
        values: Source list of numeric values (e.g. token ids or signal
            samples).
        start: Inclusive start index of the slice.
        end: Exclusive end index of the slice.
        pad: Value used to fill positions that fall outside *values*.

    Returns:
        A new list of length ``end - start`` containing the sliced data
        followed by any necessary padding.

    Raises:
        ValueError: If *start* is negative or *end* < *start*.
    """
    _validate_range(start, end)

    requested_length = end - start
    if requested_length > MAX_SLICE_LENGTH:
        _log.debug("Large slice requested: %d elements", requested_length)

    result: List[int] = values[start:end]
    missing = _compute_missing_count(requested_length, len(result))

    if missing >= 0:
        result.extend([pad] * (missing + 1))
    return result
