import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    AreaCode,
    InventoryQuantity,
    NumberType,
    RentalDuration,
    ReservationCapability,
    ReservationType,
    Service,
)
import datetime


def test_get_area_codes(tv, mock_http_from_disk):
    area_codes = tv.services.area_codes()

    area_codes_list = [x.to_api() for x in area_codes]
    assert all(
        dict_subset(area_code_test, area_code_truth) is None
        for area_code_test, area_code_truth in zip(area_codes_list, mock_http_from_disk.last_response)
    )
    assert all(isinstance(area_code, AreaCode) for area_code in area_codes)


def test_get_services(tv, mock_http_from_disk):
    services = tv.services.list(NumberType.MOBILE, ReservationType.VERIFICATION)

    services_list = [x.to_api() for x in services]
    assert all(
        dict_subset(service_test, service_truth) is None
        for service_test, service_truth in zip(services_list, mock_http_from_disk.last_response)
    )
    assert all(isinstance(service, Service) for service in services)


def test_get_rental_inventory(tv, mock_http_from_disk):
    inventory = tv.services.rental_inventory(
        duration=RentalDuration.THIRTY_DAY,
        number_type=NumberType.MOBILE,
        service_name="test_service",
        capability=ReservationCapability.SMS,
    )

    assert isinstance(inventory, InventoryQuantity)
    assert inventory.available_quantity == 37
    assert mock_http_from_disk.last_body_params == {
        "duration": RentalDuration.THIRTY_DAY.value,
        "numberType": NumberType.MOBILE.value,
        "serviceName": "test_service",
        "capability": ReservationCapability.SMS.value,
    }


def test_get_verification_inventory(tv, mock_http_from_disk):
    inventory = tv.services.verification_inventory(
        number_type=NumberType.MOBILE,
        service_name="test_service",
        capability=ReservationCapability.SMS,
    )

    assert isinstance(inventory, InventoryQuantity)
    assert inventory.available_quantity == 37
