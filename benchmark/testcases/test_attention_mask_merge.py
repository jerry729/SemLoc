import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if pytest.inst:
    from instrumented.attention_mask_merge import attention_mask_merge
else:
    from programs.attention_mask_merge import attention_mask_merge


def test_all_positions_kept():
    """When both masks fully attend, the merged mask should also fully attend."""
    mask_a = [True, True, True, True]
    mask_b = [True, True, True, True]
    result = attention_mask_merge(mask_a, mask_b)
    assert result == [True, True, True, True]


def test_all_positions_masked():
    """When both masks fully block, the merged mask should also fully block."""
    mask_a = [False, False, False]
    mask_b = [False, False, False]
    result = attention_mask_merge(mask_a, mask_b)
    assert result == [False, False, False]


def test_shape_mismatch_raises():
    """Masks of different lengths must raise a ValueError."""
    with pytest.raises(ValueError, match="shape mismatch"):
        attention_mask_merge([True, False], [True])


def test_single_element_both_true():
    """A single-element mask where both inputs keep the token."""
    result = attention_mask_merge([True], [True])
    assert result == [True]


def test_single_element_both_false():
    """A single-element mask where both inputs block the token."""
    result = attention_mask_merge([False], [False])
    assert result == [False]


def test_conjunction_blocks_when_one_mask_is_false():
    """A position should be masked out when one mask blocks it."""
    mask_a = [True, True, True]
    mask_b = [True, False, True]
    result = attention_mask_merge(mask_a, mask_b)
    assert result == [True, False, True]


def test_mixed_masks_conjunction_semantics():
    """Merged mask should retain only positions kept by both inputs."""
    mask_a = [True, False, True, False]
    mask_b = [False, True, True, False]
    result = attention_mask_merge(mask_a, mask_b)
    assert result == [False, False, True, False]


def test_causal_and_padding_mask_overlap():
    """Simulates merging a causal mask with a padding mask — only jointly
    attended positions survive."""
    causal = [True, True, True, False, False]
    padding = [True, True, False, False, False]
    result = attention_mask_merge(causal, padding)
    assert result == [True, True, False, False, False]


def test_alternating_masks_produce_no_overlap():
    """Alternating True/False masks with no shared positions should yield all False."""
    mask_a = [True, False, True, False, True, False]
    mask_b = [False, True, False, True, False, True]
    result = attention_mask_merge(mask_a, mask_b)
    assert result == [False, False, False, False, False, False]


def test_result_length_matches_input():
    """Output mask length must equal the input mask length."""
    mask_a = [True, False, True, True, False]
    mask_b = [False, False, True, True, True]
    result = attention_mask_merge(mask_a, mask_b)
    assert len(result) == 5
