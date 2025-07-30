import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    VerificationPriceCheckRequest,
    NewVerificationRequest,
    PricingSnapshot,
    ReservationCapability,
    NumberType,
    VerificationCompact,
    VerificationExpanded,
)
import datetime


def create_move_action_hook(nmethod, href):
    def move_action_to_endpoint(response, method, url, **kwargs):
        if "href" in response and "method" in response:
            response["href"] = href
            response["method"] = nmethod
        return response

    return move_action_to_endpoint


def test_create_verification(tv, mock_http_from_disk):
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/verifications/ver_string")
    )

    verification = tv.verifications.create(
        area_code_select_option=["123"],
        carrier_select_option=["carrier1"],
        service_name="test_service",
        capability=ReservationCapability.SMS,
        service_not_listed_name="Custom Service",
        max_price=1.50,
    )

    assert isinstance(verification, VerificationExpanded)
    assert dict_subset(verification.to_api(), mock_http_from_disk.last_response) is None


def test_get_verification_pricing(tv, mock_http_from_disk):
    pricing = tv.verifications.pricing(
        service_name="test_service",
        area_code=True,
        carrier=True,
        number_type=NumberType.MOBILE,
        capability=ReservationCapability.SMS,
    )

    assert isinstance(pricing, PricingSnapshot)
    assert dict_subset(pricing.to_api(), mock_http_from_disk.last_response) is None


def test_get_verification_details(tv, mock_http_from_disk):
    verification_id = "string"
    verification = tv.verifications.details(verification_id)

    assert isinstance(verification, VerificationExpanded)
    assert dict_subset(verification.to_api(), mock_http_from_disk.last_response) is None
    assert verification.id == verification_id


def test_get_verification_details_by_instance(tv, mock_http_from_disk):
    test_get_verification_details(tv, mock_http_from_disk)  # Load the verification
    verification = VerificationExpanded.from_api(mock_http_from_disk.last_response)

    verification_details = tv.verifications.details(verification)

    assert isinstance(verification_details, VerificationExpanded)
    assert dict_subset(verification_details.to_api(), mock_http_from_disk.last_response) is None


def test_get_verifications(tv, mock_http_from_disk):
    verifications = tv.verifications.list()

    verifications_list = [x.to_api() for x in verifications]
    assert all(
        dict_subset(verification_test, verification_truth) is None
        for verification_test, verification_truth in zip(verifications_list, mock_http_from_disk.last_response["data"])
    )


def test_cancel_reservation_by_id(tv, mock_http_from_disk):
    verification_id = "string"

    result = tv.verifications.cancel(verification_id)

    assert result is True


def test_cancel_reservation_by_instance(tv, mock_http_from_disk):
    test_get_verification_details(tv, mock_http_from_disk)  # Load the verification
    verification = VerificationExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.verifications.cancel(verification)

    assert result is True


def test_reactivate_verification_by_id(tv, mock_http_from_disk):
    verification_id = "string"

    result = tv.verifications.reactivate(verification_id)

    assert result is True


def test_reactivate_verification_by_instance(tv, mock_http_from_disk):
    test_get_verification_details(tv, mock_http_from_disk)  # Load the verification
    verification = VerificationExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.verifications.reactivate(verification)

    assert result is True


def test_reuse_verification_by_id(tv, mock_http_from_disk):
    verification_id = "string"

    result = tv.verifications.reuse(verification_id)

    assert result is True


def test_reuse_verification_by_instance(tv, mock_http_from_disk):
    test_get_verification_details(tv, mock_http_from_disk)  # Load the verification
    verification = VerificationExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.verifications.reuse(verification)

    assert result is True


def test_report_verification_by_id(tv, mock_http_from_disk):
    verification_id = "string"

    result = tv.verifications.report(verification_id)

    assert result is True


def test_report_verification_by_instance(tv, mock_http_from_disk):
    test_get_verification_details(tv, mock_http_from_disk)  # Load the verification
    verification = VerificationExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.verifications.report(verification)

    assert result is True
