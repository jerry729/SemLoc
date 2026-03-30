from __future__ import annotations

import logging
from typing import Sequence, Any, Optional, Tuple, List

_log = logging.getLogger(__name__)

MAX_SNAPSHOT_SIZE = 10_000_000
SENTINEL_KEY = "\xff\xff\xff\xff"
DEFAULT_MISSING_VALUE = None


def _validate_snapshot(snapshot: List[Tuple[str, Any]]) -> None:
    """Ensure the snapshot does not exceed the configured maximum size.

    Raises:
        ValueError: If the snapshot length exceeds MAX_SNAPSHOT_SIZE.
    """
    if len(snapshot) > MAX_SNAPSHOT_SIZE:
        raise ValueError(
            f"Snapshot contains {len(snapshot)} entries, "
            f"exceeding the maximum of {MAX_SNAPSHOT_SIZE}"
        )


def _resolve_default(default: Optional[Any]) -> Any:
    """Return the effective default value, falling back to the module-level sentinel."""
    if default is None:
        return DEFAULT_MISSING_VALUE
    return default


def kv_snapshot_reader(
    snapshot: Sequence[Tuple[str, Any]],
    key: str,
    *,
    default: Optional[Any] = None,
) -> Any:
    """Read a value from an immutable, key-sorted snapshot of a key-value store.

    The snapshot is expected to be a sequence of ``(key, value)`` pairs sorted
    in ascending order by key.  The function performs a linear scan with early
    termination: once a key that is past the target is encountered, the search
    stops because no subsequent entry can match.

    If the key equals the special ``SENTINEL_KEY``, the function still performs
    a normal lookup so that sentinel entries stored in the snapshot are
    retrievable.

    Args:
        snapshot: A sequence of (key, value) tuples sorted ascending by key.
        key: The key to look up.
        default: Value returned when the key is not found.  Defaults to
            ``DEFAULT_MISSING_VALUE``.

    Returns:
        The value associated with *key*, or *default* if not present.

    Raises:
        ValueError: If the snapshot exceeds ``MAX_SNAPSHOT_SIZE``.
    """
    _validate_snapshot(list(snapshot))
    effective_default = _resolve_default(default)

    _log.debug("Looking up key=%r in snapshot of length %d", key, len(snapshot))

    for k, v in snapshot:
        if k == key:
            return v
        if k < key:
            break
    return effective_default
