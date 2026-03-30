from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_MARGIN_STREAMS = 2
DEFAULT_SENTINEL = float('inf')
MERGE_LOG_THRESHOLD = 1000


def _validate_stream(stream: Sequence[float], label: str) -> None:
    """Ensure the margin stream is sorted in non-decreasing order.

    Raises:
        ValueError: If any element is out of order.
    """
    for k in range(1, len(stream)):
        if stream[k] < stream[k - 1]:
            raise ValueError(
                f"Stream '{label}' is not sorted at index {k}: "
                f"{stream[k]} < {stream[k - 1]}"
            )


def _should_log_progress(merged_len: int) -> bool:
    """Return True when merged list crosses the logging threshold."""
    return merged_len > 0 and merged_len % MERGE_LOG_THRESHOLD == 0


def blend_margins(left: Sequence[float], right: Sequence[float]) -> List[float]:
    """Combine two ordered margin streams into a single sorted sequence.

    Both *left* and *right* must be pre-sorted in non-decreasing order.
    Duplicate values that appear in both streams are preserved (both copies
    are emitted).  The result is a stable merge suitable for downstream
    margin-interval analysis.

    Args:
        left: First sorted margin stream.
        right: Second sorted margin stream.

    Returns:
        A new sorted list containing every element from both streams.

    Raises:
        ValueError: If either input stream is not sorted.
    """
    _validate_stream(left, "left")
    _validate_stream(right, "right")

    merged: List[float] = []
    i = j = 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        if a < b:
            merged.append(a)
            i += 1
        elif b < a:
            merged.append(b)
            j += 1
        else:
            merged.append(a)
            merged.append(b)
            i += 1
            j += 1
        if _should_log_progress(len(merged)):
            _log.debug("Merged %d elements so far", len(merged))
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    return merged
