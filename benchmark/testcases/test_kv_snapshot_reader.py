import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.kv_snapshot_reader import kv_snapshot_reader
else:
    from programs.kv_snapshot_reader import kv_snapshot_reader


def test_empty_snapshot_returns_default():
    """An empty snapshot should always yield the default value."""
    assert kv_snapshot_reader([], "alpha") is None


def test_empty_snapshot_returns_custom_default():
    """A custom default should be returned when the snapshot is empty."""
    assert kv_snapshot_reader([], "beta", default="missing") == "missing"


def test_single_entry_exact_match():
    """A snapshot with one entry should return its value on exact key match."""
    snapshot = [("config.version", 42)]
    assert kv_snapshot_reader(snapshot, "config.version") == 42


def test_single_entry_no_match():
    """If the single entry key differs, the default is returned."""
    snapshot = [("config.version", 42)]
    assert kv_snapshot_reader(snapshot, "config.name") is None


def test_lookup_first_key_in_sorted_snapshot():
    """The first key in a sorted snapshot should be found correctly."""
    snapshot = [("aaa", 1), ("bbb", 2), ("ccc", 3), ("ddd", 4)]
    assert kv_snapshot_reader(snapshot, "aaa") == 1


def test_lookup_middle_key_in_sorted_snapshot():
    """A key in the middle of a sorted snapshot should be retrievable."""
    snapshot = [("aaa", 1), ("bbb", 2), ("ccc", 3), ("ddd", 4)]
    assert kv_snapshot_reader(snapshot, "ccc") == 3


def test_lookup_last_key_in_sorted_snapshot():
    """The last key in a sorted snapshot should be retrievable."""
    snapshot = [("aaa", 1), ("bbb", 2), ("ccc", 3), ("ddd", 4)]
    assert kv_snapshot_reader(snapshot, "ddd") == 4


def test_missing_key_between_entries_returns_default():
    """A key that falls between existing entries should yield the default."""
    snapshot = [("aaa", 1), ("ccc", 3), ("eee", 5)]
    assert kv_snapshot_reader(snapshot, "bbb", default=-1) == -1


def test_key_beyond_all_entries_returns_default():
    """A key lexicographically after all snapshot keys should yield the default."""
    snapshot = [("aaa", 1), ("bbb", 2), ("ccc", 3)]
    assert kv_snapshot_reader(snapshot, "zzz", default="nope") == "nope"


def test_early_termination_does_not_skip_valid_match():
    """The scan should not terminate before reaching a valid matching key."""
    snapshot = [("alpha", 10), ("beta", 20), ("gamma", 30), ("zeta", 40)]
    assert kv_snapshot_reader(snapshot, "gamma") == 30
