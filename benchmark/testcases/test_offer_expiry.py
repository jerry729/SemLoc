import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
if pytest.inst:
    from instrumented.offer_expiry import offer_expiry
else:
    from programs.offer_expiry import offer_expiry


def test_missing_key_returns_default():
    """When the offer key does not exist in the store, the default value is returned."""
    store = {}
    result = offer_expiry(store, "SUMMER_SALE", now=1000.0)
    assert result is None


def test_missing_key_with_custom_default():
    """A caller-supplied default is returned for absent keys."""
    store = {}
    result = offer_expiry(store, "FLASH", now=500.0, default="N/A")
    assert result == "N/A"


def test_valid_offer_well_before_deadline():
    """An offer retrieved well before its deadline should return the stored value."""
    store = {"BF2024": ("30% off", 2000.0)}
    result = offer_expiry(store, "BF2024", now=1500.0)
    assert result == "30% off"


def test_expired_offer_returns_default():
    """An offer checked after its deadline has passed should yield the default."""
    store = {"WINTER": ("20% off", 1000.0)}
    result = offer_expiry(store, "WINTER", now=1500.0)
    assert result is None


def test_offer_at_exact_deadline_is_expired():
    """An offer checked at exactly the deadline timestamp should be treated as expired."""
    store = {"NEWYEAR": ("15% off", 1000.0)}
    result = offer_expiry(store, "NEWYEAR", now=1000.0)
    assert result is None


def test_offer_one_second_before_deadline():
    """An offer checked one second before its deadline should still be valid."""
    store = {"SPRING": ("10% off", 1000.0)}
    result = offer_expiry(store, "SPRING", now=999.0)
    assert result == "10% off"


def test_integer_deadline_at_boundary():
    """Using integer timestamps at the exact deadline should expire the offer."""
    store = {"PROMO": (42, 500)}
    result = offer_expiry(store, "PROMO", now=500)
    assert result is None


def test_invalid_store_raises_type_error():
    """A store object without a .get() method should raise TypeError."""
    with pytest.raises(TypeError):
        offer_expiry([1, 2, 3], "KEY", now=100.0)


def test_multiple_offers_independent_expiry():
    """Each offer's deadline is checked independently; one expiring does not affect another."""
    store = {
        "A": ("val_a", 1000.0),
        "B": ("val_b", 2000.0),
    }
    assert offer_expiry(store, "A", now=1000.0) is None
    assert offer_expiry(store, "B", now=1000.0) == "val_b"


def test_offer_with_zero_deadline():
    """An offer with a zero deadline should be expired at timestamp zero."""
    store = {"ZERO": ("free", 0.0)}
    result = offer_expiry(store, "ZERO", now=0.0)
    assert result is None
