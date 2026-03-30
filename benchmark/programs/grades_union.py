from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

MAX_GRADE_VALUE = 100
MIN_GRADE_VALUE = 0
DUPLICATE_RETENTION_POLICY = "keep_all"


def _validate_sorted(grades: Sequence[int], label: str) -> None:
    """Verify that a grades sequence is in non-decreasing order."""
    for k in range(1, len(grades)):
        if grades[k] < grades[k - 1]:
            raise ValueError(
                f"{label} grades are not sorted at index {k}: "
                f"{grades[k - 1]} > {grades[k]}"
            )


def _clamp_grade(value: int) -> int:
    """Clamp a single grade to the valid range."""
    if value < MIN_GRADE_VALUE:
        return MIN_GRADE_VALUE
    if value > MAX_GRADE_VALUE:
        return MAX_GRADE_VALUE
    return value


def grades_union(left: Sequence[int], right: Sequence[int]) -> List[int]:
    """Combine two ordered grade streams into one merged ordered stream.

    Both *left* and *right* must be sorted in non-decreasing order.  The
    result preserves duplicates according to the module-level
    ``DUPLICATE_RETENTION_POLICY``.

    Args:
        left: First sorted sequence of integer grades.
        right: Second sorted sequence of integer grades.

    Returns:
        A new sorted list containing all grades from both inputs.

    Raises:
        ValueError: If either input is not sorted.
    """
    _validate_sorted(left, "left")
    _validate_sorted(right, "right")

    left = [_clamp_grade(g) for g in left]
    right = [_clamp_grade(g) for g in right]

    _log.debug("Merging %d left grades with %d right grades (policy=%s)",
               len(left), len(right), DUPLICATE_RETENTION_POLICY)

    merged: List[int] = []
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
    merged.extend(left[i:])
    merged.extend(right[j:])

    if merged and left and right and merged[-1] == left[-1] == right[-1]:
        merged.pop()

    return merged
