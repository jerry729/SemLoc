import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.bump_purchase import bump_purchase
else:
    from programs.bump_purchase import bump_purchase


def test_first_purchase_creates_entry():
    """A new product key should start at 1 after its first purchase bump."""
    counters = {}
    result = bump_purchase(counters, "SKU-100")
    assert result == 1
    assert counters["SKU-100"] == 1


def test_increment_existing_counter():
    """Bumping an existing counter should increase it by exactly one."""
    counters = {"SKU-200": 3}
    result = bump_purchase(counters, "SKU-200")
    assert result == 4
    assert counters["SKU-200"] == 4


def test_no_cap_allows_unlimited_growth():
    """Without a cap the counter should grow without bound."""
    counters = {"SKU-300": 999}
    result = bump_purchase(counters, "SKU-300")
    assert result == 1000


def test_cap_well_above_current_does_not_restrict():
    """A cap far above the current value should not interfere with the increment."""
    counters = {"SKU-400": 2}
    result = bump_purchase(counters, "SKU-400", cap=100)
    assert result == 3


def test_counter_reaches_cap_exactly():
    """When the counter is one below the cap, bumping should bring it to the cap value."""
    counters = {"SKU-500": 4}
    result = bump_purchase(counters, "SKU-500", cap=5)
    assert result == 5
    assert counters["SKU-500"] == 5


def test_counter_at_cap_stays_at_cap():
    """Once at the cap, further bumps should keep the counter at the cap ceiling."""
    counters = {"SKU-600": 10}
    result = bump_purchase(counters, "SKU-600", cap=10)
    assert result == 10
    assert counters["SKU-600"] == 10


def test_counter_above_cap_is_clamped():
    """If the incremented value exceeds the cap it must be clamped to the cap."""
    counters = {"SKU-700": 10}
    result = bump_purchase(counters, "SKU-700", cap=5)
    assert result == 5
    assert counters["SKU-700"] == 5


def test_repeated_bumps_respect_cap():
    """Repeatedly bumping should never let the counter exceed the cap."""
    counters = {"SKU-800": 0}
    cap = 3
    for _ in range(10):
        result = bump_purchase(counters, "SKU-800", cap=cap)
    assert result == cap
    assert counters["SKU-800"] == cap


def test_invalid_cap_raises_value_error():
    """A cap below the minimum threshold should raise a ValueError."""
    counters = {}
    with pytest.raises(ValueError):
        bump_purchase(counters, "SKU-900", cap=0)


def test_multiple_keys_independent():
    """Counters for different keys should be updated independently."""
    counters = {"A": 1, "B": 5}
    bump_purchase(counters, "A", cap=10)
    bump_purchase(counters, "B", cap=10)
    assert counters["A"] == 2
    assert counters["B"] == 6
