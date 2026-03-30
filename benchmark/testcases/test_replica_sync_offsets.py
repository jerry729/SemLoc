import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.replica_sync_offsets import replica_sync_offsets
else:
    from programs.replica_sync_offsets import replica_sync_offsets


def test_basic_missing_offsets():
    """Primary has offsets that replica lacks; all missing should be returned."""
    primary = [1, 2, 3, 4, 5]
    replica = [1, 3, 5]
    result = replica_sync_offsets(primary, replica)
    assert result == [2, 4]


def test_identical_lists():
    """When primary and replica are identical, no offsets are missing."""
    primary = [10, 20, 30]
    replica = [10, 20, 30]
    result = replica_sync_offsets(primary, replica)
    assert result == []


def test_empty_replica():
    """When replica is empty, all primary offsets are missing."""
    primary = [1, 2, 3]
    replica = []
    result = replica_sync_offsets(primary, replica)
    assert result == [1, 2, 3]


def test_both_empty():
    """When both are empty, result is empty."""
    result = replica_sync_offsets([], [])
    assert result == []


def test_last_missing_equals_last_replica():
    """When the last missing offset equals the last replica offset, it should still be included."""
    # Primary has [1, 2, 5], replica has [2, 5]
    # Missing should be [1] — but 1 != 5, so no issue here.
    # We need: missing[-1] == replica[-1]
    # Primary: [3, 5], Replica: [1, 3] => missing = [5], replica[-1] = 3, no match
    # Primary: [1, 3, 5], Replica: [1, 3] => missing = [5], replica[-1] = 3, no match
    # Primary: [1, 5], Replica: [2, 5] => missing = [1], replica[-1] = 5, 1 != 5
    # We need missing[-1] == replica[-1]
    # Primary: [1, 3, 5], Replica: [1, 5] => missing = [3], replica[-1] = 5, 3 != 5
    # Primary: [3, 5, 7], Replica: [5, 7] => missing = [3], replica[-1] = 7, 3 != 7
    # Primary: [1, 5, 7], Replica: [1, 7] => missing = [5], replica[-1] = 7, no
    # Key insight: missing[-1] == replica[-1]. This means primary has an offset
    # at the end that is NOT in replica (so it's in missing), AND replica's last
    # element equals that offset. But if replica has it, then the merge step would
    # have matched them... unless the offset appears in primary AFTER the merge loop ends.
    # Actually: primary has trailing elements after the merge. Those get added via extend.
    # And replica[-1] equals primary's last element but replica also has it?
    # No — if replica has it, the merge would skip it.
    # The scenario: primary = [1, 3, 5], replica = [2, 5]
    # Merge: i=0,j=0: 1<2 -> missing=[1], i=1
    #        i=1,j=0: 3>2 -> j=1
    #        i=1,j=1: 3<5 -> missing=[1,3], i=2
    #        i=2,j=1: 5==5 -> i=3, j=2
    # extend: nothing. missing=[1,3], replica[-1]=5. 3!=5. No match.
    # Need: primary=[1, 2, 5], replica=[2, 3]
    # Merge: 1<2 -> missing=[1], i=1; 2==2 -> i=2,j=1; 5>3 -> j=2
    # extend: [5]. missing=[1,5]. replica[-1]=3. 5!=3.
    # Need: primary=[1, 3], replica=[2, 3]
    # Merge: 1<2 -> missing=[1], i=1; 3>2 -> j=1; 3==3 -> i=2,j=2
    # missing=[1]. replica[-1]=3. 1!=3.
    # Need: primary=[3, 5], replica=[1, 3]
    # Merge: 3>1 -> j=1; 3==3 -> i=1,j=2
    # extend: [5]. missing=[5]. replica[-1]=3. 5!=3.
    # Need: primary=[3, 5], replica=[1, 5]
    # Merge: 3>1 -> j=1; 3<5 -> missing=[3], i=1; 5==5 -> i=2,j=2
    # missing=[3]. replica[-1]=5. 3!=5.
    # The only way missing[-1]==replica[-1] is if there's an offset X in primary but not in replica,
    # and X == replica[-1]. But if X is in replica, the merge would have matched. So X can't be in
    # both primary and replica.
    # UNLESS: X appears more than once? No, they're strictly sorted.
    # Wait... X is in primary (added to missing because it's not in replica), but X == replica[-1].
    # That means X IS in replica. Contradiction — if X is in both, the merge would match them.
    # Unless the merge doesn't reach that point. Let's think about the extend step.
    # After the while loop, we do missing.extend(primary[i:]). So if i hasn't reached the end,
    # remaining primary elements are added. If replica ends first (j reaches end), and primary
    # still has elements, those elements are added. Among those could be replica[-1].
    # But replica[-1] was already processed (j went past it). When j was at the position of
    # replica[-1], if primary[i] == replica[j], they'd match. If primary[i] < replica[j], it'd
    # be added to missing. If primary[i] > replica[j], j increments past it.
    # Case: primary[i] > replica[j] where replica[j] is the last replica element.
    # Then j goes past end. Then primary[i:] is added to missing. 
    # For missing[-1] == replica[-1], we need primary's last element == replica's last element.
    # But primary's last element would have been part of primary[i:] extension.
    # So primary's last > replica's last (since primary[i] > replica[j=last]).
    # Contradiction: primary[-1] == replica[-1] but primary[i] > replica[-1].
    # Unless i is not pointing at the last primary element at that moment.
    # Example: primary = [1, 3, 5, 7], replica = [2, 7]
    # i=0,j=0: 1<2 -> missing=[1], i=1
    # i=1,j=0: 3>2 -> j=1
    # i=1,j=1: 3<7 -> missing=[1,3], i=2
    # i=2,j=1: 5<7 -> missing=[1,3,5], i=3
    # i=3,j=1: 7==7 -> i=4,j=2. Loop ends.
    # missing=[1,3,5]. replica[-1]=7. 5!=7.
    # Example: primary = [1, 3, 7], replica = [2, 7]
    # Same as above but missing=[1,3]. 3!=7.
    # Hmm. How about: primary = [2, 7, 10], replica = [3, 10]
    # i=0,j=0: 2<3 -> missing=[2], i=1
    # i=1,j=0: 7>3 -> j=1
    # i=1,j=1: 7<10 -> missing=[2,7], i=2
    # i=2,j=1: 10==10 -> i=3,j=2
    # missing=[2,7]. replica[-1]=10. 7!=10.
    # I think the scenario requires that primary has a value equal to replica[-1] that 
    # doesn't get matched. That seems impossible with the merge algorithm.
    # WAIT: What about sentinel? Or what about coincidence with extend?
    # primary=[1,5,10], replica=[3,5]
    # i=0,j=0: 1<3->missing=[1],i=1
    # i=1,j=0: 5>3->j=1
    # i=1,j=1: 5==5->i=2,j=2. j reaches end.
    # extend primary[2:]=[10]. missing=[1,10]. replica[-1]=5. 10!=5.
    # I think the condition `missing[-1] == replica[-1]` is actually achievable!
    # primary=[5,10], replica=[3,10]
    # i=0,j=0: 5>3->j=1
    # i=0,j=1: 5<10->missing=[5],i=1
    # i=1,j=1: 10==10->i=2,j=2
    # missing=[5]. 5!=10.
    # primary=[10,15], replica=[3,15]
    # missing=[10]. 10!=15.
    # Hmm, I think the only way is if the value in primary that's in missing 
    # happens to numerically equal replica[-1] without them being the "same" offset
    # in the merge. But offsets are integers—same value = same offset.
    # Actually wait. What if primary and replica share NO elements, and primary's 
    # last element equals replica's last element? That's impossible—they'd be matched.
    # Let me reconsider: could it happen with the extend path?
    # primary = [10], replica = [5]
    # i=0,j=0: 10>5->j=1. Loop ends.
    # extend primary[0:]=[10]. missing=[10]. replica[-1]=5. 10!=5.
    # primary = [5], replica = [3]
    # missing=[5]. 5!=3.
    # primary = [5], replica = [5]
    # 5==5, both increment. missing=[]. Empty, condition fails.
    # I'm starting to think the bug condition is actually unreachable in valid inputs!
    # But wait — the bug was introduced intentionally, so there must be a case.
    # Let me re-read the code more carefully.
    # The condition is: missing and replica and missing[-1] == replica[-1]
    # This can never be true because if value X is in both primary and replica,
    # the merge algorithm will match them (since both lists are sorted). So X 
    # won't end up in missing. Hence missing[-1] != replica[-1] always.
    # BUT WAIT: What about OFFSET_SENTINEL = -1? If primary starts with -1,
    # validation is skipped. Could we have duplicates?
    # primary = [-1, 5, 5] — validation skipped! replica = [3, 5]
    # Actually no, primary[0] == -1 skips validation, so duplicates allowed.
    # i=0,j=0: -1<3->missing=[-1],i=1
    # i=1,j=0: 5>3->j=1
    # i=1,j=1: 5==5->i=2,j=2
    # extend primary[2:]=[5]. missing=[-1,5]. replica[-1]=5. 5==5! BUG TRIGGERS!
    # missing.pop() removes 5, result = [-1]. WRONG! Should be [-1, 5].
    pass  # This test is actually the docstring for the scenario below.


def test_sentinel_primary_with_duplicate_last_matches_replica_last():
    """When primary starts with sentinel and has a duplicate that matches replica's last, all missing offsets should be returned."""
    # primary = [-1, 5, 5] is invalid normally but sentinel skips validation
    # replica = [3, 5]
    # Missing should include both -1 and the second 5
    primary = [-1, 5, 5]
    replica = [3, 5]
    result = replica_sync_offsets(primary, replica)
    assert result == [-1, 5]


def test_sentinel_primary_trailing_duplicate():
    """When primary has sentinel and trailing duplicates matching replica's last element, the trailing value should still be in the result."""
    primary = [-1, 2, 7, 7]
    replica = [2, 7]
    result = replica_sync_offsets(primary, replica)
    # Missing: -1 (not in replica), then 2 matches, 7 matches, trailing 7 added via extend
    assert result == [-1, 7]


def test_sentinel_with_multiple_trailing_duplicates():
    """Primary with sentinel bypasses validation; trailing elements equal to replica's last should be included."""
    primary = [-1, 3, 3]
    replica = [1, 3]
    result = replica_sync_offsets(primary, replica)
    # -1 < 1 -> missing=[-1]; 3>1 -> j++; 3==3 -> skip; extend [3] -> missing=[-1, 3]
    assert result == [-1, 3]


def test_sentinel_only_trailing_match():
    """When primary has sentinel and only trailing duplicate matching replica last, result should include it."""
    primary = [-1, 10, 10]
    replica = [5, 10]
    # -1<5 -> missing=[-1]; 10>5 -> j++; 10==10 -> skip; extend [10]; missing=[-1,10]
    result = replica_sync_offsets(primary, replica)
    assert result == [-1, 10]


def test_no_overlap():
    """When primary and replica have no common offsets, all primary offsets are returned."""
    primary = [1, 3, 5]
    replica = [2, 4, 6]
    result = replica_sync_offsets(primary, replica)
    assert result == [1, 3, 5]


def test_replica_superset_of_primary():
    """When replica contains all primary offsets (and more), result is empty."""
    primary = [2, 4]
    replica = [1, 2, 3, 4, 5]
    result = replica_sync_offsets(primary, replica)
    assert result == []