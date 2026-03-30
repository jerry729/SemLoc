import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.shift_demand import shift_demand
else:
    from programs.shift_demand import shift_demand


def test_shape_mismatch_raises():
    """Vectors of different length must be rejected."""
    with pytest.raises(ValueError, match="shape mismatch"):
        shift_demand([0.5, 0.5], [0.3, 0.3, 0.4])


def test_empty_allocation_raises():
    """An empty demand vector is invalid."""
    with pytest.raises(ValueError, match="empty allocation"):
        shift_demand([], [])


def test_invalid_damping_raises():
    """Damping outside [0, 1] must be rejected."""
    with pytest.raises(ValueError):
        shift_demand([0.5, 0.5], [0.3, 0.7], damping=1.5)


def test_damping_zero_preserves_current():
    """Zero damping means no movement toward the target; output equals input normalised."""
    result = shift_demand([0.5, 0.5], [0.8, 0.2], damping=0.0)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_output_sums_to_one_uniform():
    """The returned demand mix must always sum to 1.0."""
    result = shift_demand([0.25, 0.25, 0.25, 0.25], [0.4, 0.3, 0.2, 0.1])
    assert abs(sum(result) - 1.0) < 1e-9


def test_output_sums_to_one_skewed():
    """Even with highly skewed inputs the output must sum to 1.0."""
    result = shift_demand([0.9, 0.05, 0.05], [0.1, 0.1, 0.8], damping=0.7)
    assert abs(sum(result) - 1.0) < 1e-9


def test_full_damping_reaches_target():
    """With damping=1.0 the output must exactly match the target distribution."""
    target = [0.6, 0.3, 0.1]
    result = shift_demand([0.2, 0.3, 0.5], target, damping=1.0)
    for r, t in zip(result, target):
        assert abs(r - t) < 1e-9


def test_normalisation_with_non_unit_inputs():
    """When current and target do not sum to 1, the output must still be normalised."""
    result = shift_demand([1.0, 1.0], [2.0, 2.0], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert abs(result[0] - 0.5) < 1e-9


def test_two_elements_proportions():
    """The relative proportions should reflect partial movement toward the target."""
    result = shift_demand([0.5, 0.5], [1.0, 0.0], damping=0.5)
    assert abs(sum(result) - 1.0) < 1e-9
    assert result[0] > result[1]


def test_single_element_stays_one():
    """A single-element demand mix must remain exactly 1.0 after shift."""
    result = shift_demand([1.0], [1.0], damping=0.5)
    assert abs(result[0] - 1.0) < 1e-9
