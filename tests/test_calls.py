import pytest
from .fixtures import (
    tv,
    mock_http_from_disk,
    mock_http,
    dict_subset,
    verification_compact,
    verification_expanded,
    renewable_rental_compact,
    renewable_rental_expanded,
    nonrenewable_rental_compact,
    nonrenewable_rental_expanded,
)
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    Call,
    TwilioCallingContextDto,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    RenewableRentalCompact,
    RenewableRentalExpanded,
    VerificationCompact,
    VerificationExpanded,
    ReservationType,
    Reservation,
)
import datetime
from unittest.mock import patch


def test_list_calls_by_to_number(tv, mock_http_from_disk):
    """Test listing calls filtered by destination phone number."""
    calls_list = tv.calls.list(to_number="+1234567890")

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_reservation_type(tv, mock_http_from_disk):
    """Test listing calls filtered by reservation type."""
    calls_list = tv.calls.list(to_number="+1234567890", reservation_type=ReservationType.RENEWABLE)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_renewable_rental_compact(tv, mock_http_from_disk, renewable_rental_compact):
    """Test listing calls for a renewable rental compact object."""
    calls_list = tv.calls.list(data=renewable_rental_compact)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_renewable_rental_expanded(tv, mock_http_from_disk, renewable_rental_expanded):
    """Test listing calls for a renewable rental expanded object."""
    calls_list = tv.calls.list(data=renewable_rental_expanded)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_nonrenewable_rental_compact(tv, mock_http_from_disk, nonrenewable_rental_compact):
    """Test listing calls for a nonrenewable rental compact object."""
    calls_list = tv.calls.list(data=nonrenewable_rental_compact)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_nonrenewable_rental_expanded(tv, mock_http_from_disk, nonrenewable_rental_expanded):
    """Test listing calls for a nonrenewable rental expanded object."""
    calls_list = tv.calls.list(data=nonrenewable_rental_expanded)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_verification_compact(tv, mock_http_from_disk, verification_compact):
    """Test listing calls for a verification compact object."""
    calls_list = tv.calls.list(data=verification_compact)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_by_verification_expanded(tv, mock_http_from_disk, verification_expanded):
    """Test listing calls for a verification expanded object."""
    calls_list = tv.calls.list(data=verification_expanded)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_all(tv, mock_http_from_disk):
    """Test listing all calls without any filters."""
    calls_list = tv.calls.list()

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_with_reservation_object(tv, mock_http_from_disk):
    """Test listing calls with a generic Reservation object."""
    reservation = Reservation(
        id="reservation_123",
        reservation_type=ReservationType.RENEWABLE,
        service_name="allservices",
    )

    calls_list = tv.calls.list(data=reservation)

    call_messages = [x.to_api() for x in calls_list]
    assert all(
        dict_subset(call_test, call_truth) is None
        for call_test, call_truth in zip(call_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_calls_error_data_and_to_number(tv):
    """Test that providing both data and to_number raises ValueError."""
    rental = RenewableRentalCompact(
        created_at=datetime.datetime.now(datetime.timezone.utc),
        id="rental_123",
        sale_id="sale_123",
        service_name="test_service",
        state="RENEWABLE_ACTIVE",
        billing_cycle_id="cycle_123",
        is_included_for_next_renewal=True,
        number="+1234567890",
        always_on=True,
    )

    with pytest.raises(ValueError, match="Cannot specify both rental/verification data and to_number"):
        tv.calls.list(data=rental, to_number="+0987654321")


def test_list_calls_error_reservation_type_with_data(tv):
    """Test that providing reservation_type with data raises ValueError."""
    rental = RenewableRentalCompact(
        created_at=datetime.datetime.now(datetime.timezone.utc),
        id="rental_123",
        sale_id="sale_123",
        service_name="test_service",
        state="RENEWABLE_ACTIVE",
        billing_cycle_id="cycle_123",
        is_included_for_next_renewal=True,
        number="+1234567890",
        always_on=True,
    )

    with pytest.raises(ValueError, match="Cannot specify reservation_type when using a rental or verification object"):
        tv.calls.list(data=rental, reservation_type=ReservationType.RENEWABLE)


def test_open_call_session_with_reservation_id(tv, mock_http_from_disk):
    """Test opening a call session with a reservation ID string."""
    reservation_id = "reservation_123"

    twilio_context = tv.calls.open_call_session(reservation_id)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == reservation_id


def test_open_call_session_with_renewable_rental_compact(tv, mock_http_from_disk, renewable_rental_compact):
    """Test opening a call session with a RenewableRentalCompact object."""
    twilio_context = tv.calls.open_call_session(renewable_rental_compact)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == renewable_rental_compact.id


def test_open_call_session_with_renewable_rental_expanded(tv, mock_http_from_disk, renewable_rental_expanded):
    """Test opening a call session with a RenewableRentalExpanded object."""
    twilio_context = tv.calls.open_call_session(renewable_rental_expanded)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == renewable_rental_expanded.id


def test_open_call_session_with_nonrenewable_rental_compact(tv, mock_http_from_disk, nonrenewable_rental_compact):
    """Test opening a call session with a NonrenewableRentalCompact object."""
    twilio_context = tv.calls.open_call_session(nonrenewable_rental_compact)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == nonrenewable_rental_compact.id


def test_open_call_session_with_nonrenewable_rental_expanded(tv, mock_http_from_disk, nonrenewable_rental_expanded):
    """Test opening a call session with a NonrenewableRentalExpanded object."""
    twilio_context = tv.calls.open_call_session(nonrenewable_rental_expanded)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == nonrenewable_rental_expanded.id


def test_open_call_session_with_verification_compact(tv, mock_http_from_disk, verification_compact):
    """Test opening a call session with a VerificationCompact object."""
    twilio_context = tv.calls.open_call_session(verification_compact)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == verification_compact.id


def test_open_call_session_with_verification_expanded(tv, mock_http_from_disk, verification_expanded):
    """Test opening a call session with a VerificationExpanded object."""
    twilio_context = tv.calls.open_call_session(verification_expanded)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == verification_expanded.id


def test_open_call_session_with_reservation_object(tv, mock_http_from_disk):
    """Test opening a call session with a generic Reservation object."""
    reservation = Reservation(
        id="reservation_123",
        reservation_type=ReservationType.RENEWABLE,
        service_name="allservices",
    )

    twilio_context = tv.calls.open_call_session(reservation)

    assert isinstance(twilio_context, TwilioCallingContextDto)
    # Verify the request was made with correct reservation ID
    assert mock_http_from_disk.last_body_params["reservationId"] == reservation.id


def test_open_call_session_invalid_reservation_none(tv):
    """Test that providing None reservation raises ValueError."""
    with pytest.raises(ValueError, match="reservation_id must be a valid ID or instance of Reservation/Verification"):
        tv.calls.open_call_session(None)


def test_open_call_session_invalid_reservation_empty_string(tv):
    """Test that providing empty string reservation raises ValueError."""
    with pytest.raises(ValueError, match="reservation_id must be a valid ID or instance of Reservation/Verification"):
        tv.calls.open_call_session("")


def test_open_call_session_invalid_reservation_non_string(tv):
    """Test that providing non-string reservation raises ValueError."""
    with pytest.raises(ValueError, match="reservation_id must be a valid ID or instance of Reservation/Verification"):
        tv.calls.open_call_session(123)
