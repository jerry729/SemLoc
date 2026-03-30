import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.file_chunk_stitch import file_chunk_stitch
else:
    from programs.file_chunk_stitch import file_chunk_stitch


def test_empty_chunk_list_returns_empty_bytes():
    """An empty chunk list should produce an empty payload."""
    assert file_chunk_stitch([]) == b""


def test_negative_index_raises_value_error():
    """Chunks with negative indices are invalid and must be rejected."""
    with pytest.raises(ValueError):
        file_chunk_stitch([(-1, b"bad")])


def test_non_bytes_data_raises_type_error():
    """Chunk data that is not bytes-like must raise TypeError."""
    with pytest.raises(TypeError):
        file_chunk_stitch([(0, "not bytes")])


def test_chunks_are_sorted_by_index():
    """Chunks provided out of order must be reassembled in index order."""
    chunks = [(2, b"world"), (0, b"hello"), (1, b" ")]
    result = file_chunk_stitch(chunks)
    assert result == b"hello world"


def test_single_chunk_preserves_content():
    """A single chunk should be returned as-is without truncation."""
    result = file_chunk_stitch([(0, b"onlychunk")])
    assert result == b"onlychunk"


def test_two_chunks_full_content():
    """Two chunks stitched together must contain all original bytes."""
    chunks = [(0, b"AB"), (1, b"CD")]
    result = file_chunk_stitch(chunks)
    assert result == b"ABCD"


def test_multiple_chunks_total_length():
    """The stitched payload length must equal the sum of all chunk lengths."""
    chunks = [(0, b"aaa"), (1, b"bbb"), (2, b"ccc")]
    result = file_chunk_stitch(chunks)
    assert len(result) == 9


def test_binary_data_integrity():
    """Binary data including null bytes must survive stitching intact."""
    chunks = [(0, b"\x00\x01"), (1, b"\x02\x03")]
    result = file_chunk_stitch(chunks)
    assert result == b"\x00\x01\x02\x03"


def test_single_byte_chunks_all_preserved():
    """Each single-byte chunk must appear in the final result."""
    chunks = [(i, bytes([i])) for i in range(5)]
    result = file_chunk_stitch(chunks)
    assert result == b"\x00\x01\x02\x03\x04"


def test_large_chunk_count_preserves_data():
    """Stitching many small chunks must not lose any trailing data."""
    n = 100
    chunks = [(i, b"x") for i in range(n)]
    result = file_chunk_stitch(chunks)
    assert result == b"x" * n
