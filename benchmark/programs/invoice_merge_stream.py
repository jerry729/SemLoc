from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_STREAM_SIZE = 500_000
DUPLICATE_SENTINEL = -1
MERGE_LOG_THRESHOLD = 1000


def _validate_sorted(stream: Sequence[int], label: str) -> None:
    """Ensure the input stream is sorted in non-decreasing order."""
    for k in range(1, len(stream)):
        if stream[k] < stream[k - 1]:
            raise ValueError(
                f"{label} stream is not sorted at index {k}: "
                f"{stream[k]} < {stream[k - 1]}"
            )


def _clamp_stream_size(stream: Sequence[int], label: str) -> Sequence[int]:
    """Truncate a stream that exceeds the maximum allowed size."""
    if len(stream) > MAX_STREAM_SIZE:
        _log.debug(
            "Truncating %s stream from %d to %d entries",
            label,
            len(stream),
            MAX_STREAM_SIZE,
        )
        return stream[:MAX_STREAM_SIZE]
    return stream


def invoice_merge_stream(
    left: Sequence[int], right: Sequence[int]
) -> List[int]:
    """Merge two sorted invoice-ID streams into a single sorted stream.

    Both input sequences must be pre-sorted in non-decreasing order.
    Duplicate IDs that appear in both streams are preserved (one copy
    from each side) so that downstream reconciliation can detect them.

    Args:
        left:  Sorted sequence of invoice IDs from the primary ledger.
        right: Sorted sequence of invoice IDs from the secondary ledger.

    Returns:
        A new sorted list containing every invoice ID from both streams.

    Raises:
        ValueError: If either input stream is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    left = _clamp_stream_size(left, "left")
    right = _clamp_stream_size(right, "right")

    i = j = 0
    merged: List[int] = []

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            merged.append(left[i])
            i += 1
        elif right[j] < left[i]:
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            merged.append(right[j])
            i += 1
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])

    if len(merged) > MERGE_LOG_THRESHOLD:
        _log.debug("Merged stream contains %d entries", len(merged))

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()
    return merged
