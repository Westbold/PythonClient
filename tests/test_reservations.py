import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    RenewableRentalCompact,
    RenewableRentalExpanded,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    BackOrderReservationCompact,
    BackOrderReservationExpanded,
    LineHealth,
    RentalExtensionRequest,
    RentalDuration,
    NewRentalRequest,
    RentalPriceCheckRequest,
    PricingSnapshot,
    NumberType,
    ReservationCapability,
    ReservationSaleExpanded,
    RenewableRentalUpdateRequest,
    NonrenewableRentalUpdateRequest,
)
import datetime


def create_move_action_hook(nmethod, href):
    def move_action_to_endpoint(response, method, url, **kwargs):
        if "href" in response and "method" in response:
            response["href"] = href
            response["method"] = nmethod
        return response

    return move_action_to_endpoint


def test_create_rental_reservation(tv, mock_http_from_disk):
    mock_http_from_disk.add_hook(create_move_action_hook("get", "https://textverified.com/api/pub/v2/sales/rs_string"))

    reservation_sale = tv.reservations.create(
        allow_back_order_reservations=True,
        always_on=False,
        area_code_select_option=["123"],
        duration=RentalDuration.THIRTY_DAY,
        is_renewable=True,
        number_type=NumberType.MOBILE,
        billing_cycle_id_to_assign_to="billing_cycle_id",
        service_name="test_service",
        capability=ReservationCapability.SMS,
    )

    assert isinstance(reservation_sale, ReservationSaleExpanded)
    assert dict_subset(reservation_sale.to_api(), mock_http_from_disk.last_response) is None


def test_get_rental_pricing(tv, mock_http_from_disk):
    pricing = tv.reservations.pricing(
        service_name="test_service",
        area_code=True,
        number_type=NumberType.MOBILE,
        capability=ReservationCapability.SMS,
        always_on=False,
        call_forwarding=False,
        billing_cycle_id_to_assign_to="billing_cycle_id",
        is_renewable=True,
        duration=RentalDuration.THIRTY_DAY,
    )

    assert isinstance(pricing, PricingSnapshot)
    assert dict_subset(pricing.to_api(), mock_http_from_disk.last_response) is None


def test_get_backorder_reservation(tv, mock_http_from_disk):
    reservation_id = "string"
    backorder_reservation = tv.reservations.backorder(reservation_id)

    assert isinstance(backorder_reservation, BackOrderReservationExpanded)
    assert dict_subset(backorder_reservation.to_api(), mock_http_from_disk.last_response) is None
    assert backorder_reservation.id == reservation_id


def test_get_reservation_details(tv, mock_http_from_disk):
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/reservations/rental/nonrenewable/string")
    )
    reservation_id = "string"
    reservation_details = tv.reservations.details(reservation_id)

    assert isinstance(reservation_details, (RenewableRentalExpanded, NonrenewableRentalExpanded))
    assert dict_subset(reservation_details.to_api(), mock_http_from_disk.last_response) is None
    assert reservation_details.id == reservation_id


def test_get_renewable_reservations(tv, mock_http_from_disk):
    reservations = tv.reservations.list_renewable()

    reservations_list = [x.to_api() for x in reservations]
    assert all(
        dict_subset(reservation_test, reservation_truth) is None
        for reservation_test, reservation_truth in zip(reservations_list, mock_http_from_disk.last_response["data"])
    )


def test_get_nonrenewable_reservations(tv, mock_http_from_disk):
    reservations = tv.reservations.list_nonrenewable()

    reservations_list = [x.to_api() for x in reservations]
    assert all(
        dict_subset(reservation_test, reservation_truth) is None
        for reservation_test, reservation_truth in zip(reservations_list, mock_http_from_disk.last_response["data"])
    )


def test_get_renewable_reservation_details(tv, mock_http_from_disk):
    reservation_id = "string"
    reservation_details = tv.reservations.renewable_details(reservation_id)

    assert isinstance(reservation_details, RenewableRentalExpanded)
    assert dict_subset(reservation_details.to_api(), mock_http_from_disk.last_response) is None
    assert reservation_details.id == reservation_id


def test_get_nonrenewable_reservation_details(tv, mock_http_from_disk):
    reservation_id = "string"
    reservation_details = tv.reservations.nonrenewable_details(reservation_id)

    assert isinstance(reservation_details, NonrenewableRentalExpanded)
    assert dict_subset(reservation_details.to_api(), mock_http_from_disk.last_response) is None
    assert reservation_details.id == reservation_id


def test_check_reservation_health(tv, mock_http_from_disk):
    reservation_id = "string"
    health = tv.reservations.check_health(reservation_id)

    assert isinstance(health, LineHealth)
    assert dict_subset(health.to_api(), mock_http_from_disk.last_response) is None


def test_update_renewable_reservation_by_id(tv, mock_http_from_disk):
    reservation_id = "string"

    result = tv.reservations.update_renewable(
        reservation_id, user_notes="Updated notes", include_for_renewal=True, mark_all_sms_read=False
    )

    assert result is True
    assert mock_http_from_disk.last_body_params["userNotes"] == "Updated notes"
    assert mock_http_from_disk.last_body_params["includeForRenewal"] is True
    assert mock_http_from_disk.last_body_params["markAllSmsRead"] is False


def test_update_renewable_reservation_by_instance(tv, mock_http_from_disk):
    test_get_renewable_reservation_details(tv, mock_http_from_disk)  # Load the reservation
    reservation = RenewableRentalExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.reservations.update_renewable(reservation, user_notes="Instance update", include_for_renewal=False)

    assert result is True
    assert mock_http_from_disk.last_body_params["userNotes"] == "Instance update"
    assert mock_http_from_disk.last_body_params["includeForRenewal"] is False


def test_update_nonrenewable_reservation_by_id(tv, mock_http_from_disk):
    reservation_id = "string"

    result = tv.reservations.update_nonrenewable(
        reservation_id, user_notes="Nonrenewable notes", mark_all_sms_read=True
    )

    assert result is True
    assert mock_http_from_disk.last_body_params["userNotes"] == "Nonrenewable notes"
    assert mock_http_from_disk.last_body_params["markAllSmsRead"] is True


def test_update_nonrenewable_reservation_by_instance(tv, mock_http_from_disk):
    test_get_nonrenewable_reservation_details(tv, mock_http_from_disk)  # Load the reservation
    reservation = NonrenewableRentalExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.reservations.update_nonrenewable(reservation, user_notes="Instance nonrenewable update")

    assert result is True
    assert mock_http_from_disk.last_body_params["userNotes"] == "Instance nonrenewable update"


def test_refund_renewable_reservation_by_id(tv, mock_http_from_disk):
    reservation_id = "string"

    result = tv.reservations.refund_renewable(reservation_id)

    assert result is True


def test_refund_renewable_reservation_by_instance(tv, mock_http_from_disk):
    test_get_renewable_reservation_details(tv, mock_http_from_disk)  # Load the reservation
    reservation = RenewableRentalExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.reservations.refund_renewable(reservation)

    assert result is True


def test_refund_nonrenewable_reservation_by_id(tv, mock_http_from_disk):
    reservation_id = "string"

    result = tv.reservations.refund_nonrenewable(reservation_id)

    assert result is True


def test_refund_nonrenewable_reservation_by_instance(tv, mock_http_from_disk):
    test_get_nonrenewable_reservation_details(tv, mock_http_from_disk)  # Load the reservation
    reservation = NonrenewableRentalExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.reservations.refund_nonrenewable(reservation)

    assert result is True


def test_renew_overdue_renewable_reservation_by_id(tv, mock_http_from_disk):
    reservation_id = "string"

    result = tv.reservations.renew_overdue(reservation_id)

    assert result is True


def test_renew_overdue_renewable_reservation_by_instance(tv, mock_http_from_disk):
    test_get_renewable_reservation_details(tv, mock_http_from_disk)  # Load the reservation
    reservation = RenewableRentalExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.reservations.renew_overdue(reservation)

    assert result is True


def test_extend_nonrenewable_reservation(tv, mock_http_from_disk):
    rental_id = "string"

    result = tv.reservations.extend_nonrenewable(extension_duration=RentalDuration.THIRTY_DAY, rental_id=rental_id)

    assert result is True
    assert mock_http_from_disk.last_body_params["extensionDuration"] == RentalDuration.THIRTY_DAY.value
    assert mock_http_from_disk.last_body_params["rentalId"] == rental_id
