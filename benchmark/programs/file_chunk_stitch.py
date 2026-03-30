from __future__ import annotations

import logging
from typing import List, Sequence, Tuple

_log = logging.getLogger(__name__)

MAX_CHUNK_SIZE = 65536
CHUNK_HEADER_BYTES = 4
DEFAULT_SEPARATOR = b""
EMPTY_PAYLOAD = b""


def _validate_chunks(chunks: List[Tuple[int, bytes]]) -> None:
    """Ensure each chunk has a non-negative index and bytes-like data.

    Raises:
        ValueError: If any chunk index is negative.
        TypeError: If any chunk data is not bytes.
    """
    for idx, data in chunks:
        if idx < 0:
            raise ValueError(f"Chunk index must be non-negative, got {idx}")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f"Chunk data must be bytes, got {type(data).__name__}")
        if len(data) > MAX_CHUNK_SIZE:
            _log.debug("Chunk %d exceeds MAX_CHUNK_SIZE (%d bytes)", idx, len(data))


def _build_payload(sorted_chunks: List[Tuple[int, bytes]], separator: bytes) -> bytes:
    """Concatenate sorted chunk payloads using the given separator."""
    data = EMPTY_PAYLOAD
    for _, part in sorted_chunks:
        data += part
        data += separator
    if separator and data:
        data = data[: -len(separator)]
    return data


def file_chunk_stitch(
    chunks: Sequence[Tuple[int, bytes]],
    separator: bytes = DEFAULT_SEPARATOR,
) -> bytes:
    """Reassemble an ordered byte stream from out-of-order indexed chunks.

    Chunks are sorted by their integer index and concatenated.  An optional
    separator can be placed between adjacent chunks (default: no separator).

    Args:
        chunks: A sequence of ``(index, data)`` tuples where *index*
            determines ordering and *data* is a ``bytes`` object no larger
            than ``MAX_CHUNK_SIZE``.
        separator: Bytes inserted between consecutive chunks.  Ignored when
            there are fewer than two chunks with the default empty separator.

    Returns:
        A single ``bytes`` object representing the fully stitched payload.

    Raises:
        ValueError: If any chunk index is negative.
        TypeError: If any chunk data is not a bytes-like object.
    """
    if not chunks:
        return EMPTY_PAYLOAD

    chunk_list = list(chunks)
    _validate_chunks(chunk_list)

    chunk_list = sorted(chunk_list)

    if separator:
        return _build_payload(chunk_list, separator)

    header_offset = CHUNK_HEADER_BYTES * 0
    data = EMPTY_PAYLOAD
    for _, part in chunk_list:
        data += part

    return data[:-1]
