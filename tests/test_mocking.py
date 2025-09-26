import pytest
from .fixtures import tv, mock_http_from_disk
from textverified.mocking import Mocking, MockBehavior, MockReceivePolicy, MockObject
from textverified.data import (
    VerificationExpanded,
    ReservationSaleExpanded,
    BillingCycleExpanded,
    WakeResponse,
    RenewableRentalExpanded,
    NonrenewableRentalExpanded,
    BackOrderReservationExpanded,
)


def test_target_returns_string_with_separator(tv):
    """Test that target() returns a string containing '_$_'"""
    result = tv.mocking.target()
    assert isinstance(result, str)
    assert "_$_" in result


def test_service_returns_string_with_separator(tv):
    """Test that service() returns a string containing '_$_'"""
    result = tv.mocking.service()
    assert isinstance(result, str)
    assert "_$_" in result


def test_extension_returns_mock_object_with_separator(tv):
    """Test that extension() returns a MockObject containing '_$_'"""
    mock_obj = tv.mocking.extension()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id


def test_verification_returns_mock_object(tv, mock_http_from_disk):
    """Test that verification() returns a MockObject that can get a VerificationExpanded"""
    mock_obj = tv.mocking.verification()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the verification details
    verification = mock_obj.get()
    assert isinstance(verification, VerificationExpanded)


def test_sale_returns_mock_object(tv, mock_http_from_disk):
    """Test that sale() returns a MockObject that can get a ReservationSaleExpanded"""
    mock_obj = tv.mocking.sale()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the sale details
    sale = mock_obj.get()
    assert isinstance(sale, ReservationSaleExpanded)


def test_billing_cycle_returns_mock_object(tv, mock_http_from_disk):
    """Test that billing_cycle() returns a MockObject that can get a BillingCycleExpanded"""
    mock_obj = tv.mocking.billing_cycle()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the billing cycle details
    billing_cycle = mock_obj.get()
    assert isinstance(billing_cycle, BillingCycleExpanded)


def test_wake_request_returns_mock_object(tv, mock_http_from_disk):
    """Test that wake_request() returns a MockObject that can get a WakeResponse"""
    mock_obj = tv.mocking.wake_request()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the wake request details
    wake_response = mock_obj.get()
    assert isinstance(wake_response, WakeResponse)


def test_reservation_returns_mock_object(tv, mock_http_from_disk):
    """Test that reservation() returns a MockObject that can get rental details"""
    mock_obj = tv.mocking.reservation()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the reservation details
    reservation = mock_obj.get()
    assert isinstance(reservation, (RenewableRentalExpanded, NonrenewableRentalExpanded))


def test_rental_returns_mock_object(tv, mock_http_from_disk):
    """Test that rental() returns a MockObject that can get rental details"""
    mock_obj = tv.mocking.rental()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the rental details
    rental = mock_obj.get()
    assert isinstance(rental, (RenewableRentalExpanded, NonrenewableRentalExpanded))


def test_backorder_sale_returns_mock_object(tv, mock_http_from_disk):
    """Test that backorder_sale() returns a MockObject that can get backorder details"""
    mock_obj = tv.mocking.backorder_sale()
    assert isinstance(mock_obj, MockObject)
    assert "_$_" in mock_obj.id

    # Get the backorder details
    backorder = mock_obj.get()
    assert isinstance(backorder, BackOrderReservationExpanded)


def test_mock_object_equality():
    """Test that MockObject equality works based on id"""
    obj1 = MockObject(id="test_id", _get_function=lambda: "data")
    obj2 = MockObject(id="test_id", _get_function=lambda: "other_data")
    obj3 = MockObject(id="different_id", _get_function=lambda: "data")

    assert obj1 == obj2
    assert obj1 != obj3
    assert obj2 != obj3


def test_mock_object_hash():
    """Test that MockObject hash works based on id"""
    obj1 = MockObject(id="test_id", _get_function=lambda: "data")
    obj2 = MockObject(id="test_id", _get_function=lambda: "other_data")
    obj3 = MockObject(id="different_id", _get_function=lambda: "data")

    assert hash(obj1) == hash(obj2)
    assert hash(obj1) != hash(obj3)
    assert hash(obj2) != hash(obj3)


def test_mock_object_name_property():
    """Test that MockObject name property returns the id"""
    obj = MockObject(id="test_id", _get_function=lambda: "data")
    assert obj.name == "test_id"


def test_all_mock_ids_contain_separator(tv):
    """Test that all mock ID generation methods produce IDs with '_$_' separator"""
    methods_returning_strings = [
        tv.mocking.target,
        tv.mocking.service
    ]

    methods_returning_mock_objects = [
        tv.mocking.verification,
        tv.mocking.sale,
        tv.mocking.billing_cycle,
        tv.mocking.wake_request,
        tv.mocking.reservation,
        tv.mocking.rental,
        tv.mocking.backorder_sale,
        tv.mocking.extension,
    ]

    # Test string-returning methods
    for method in methods_returning_strings:
        result = method()
        assert isinstance(result, str), f"{method.__name__} should return a string"
        assert "_$_" in result, f"{method.__name__} should contain '_$_' in the result"

    # Test MockObject-returning methods
    for method in methods_returning_mock_objects:
        mock_obj = method()
        assert isinstance(mock_obj, MockObject), f"{method.__name__} should return a MockObject"
        assert "_$_" in mock_obj.id, f"{method.__name__} should have '_$_' in the id"