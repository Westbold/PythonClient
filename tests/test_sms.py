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
    Sms,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    RenewableRentalCompact,
    RenewableRentalExpanded,
    VerificationCompact,
    VerificationExpanded,
    ReservationType,
    SendSmsRequest,
    ReplySmsRequest,
)
import datetime
import time
from unittest.mock import patch


def test_list_sms_by_to_number(tv, mock_http_from_disk):
    sms_list = tv.sms.list(to_number="+1234567890")

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_reservation_type(tv, mock_http_from_disk):
    sms_list = tv.sms.list(to_number="+1234567890", reservation_type=ReservationType.RENEWABLE)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_renewable_rental_compact(tv, mock_http_from_disk, renewable_rental_compact):
    sms_list = tv.sms.list(data=renewable_rental_compact)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_renewable_rental_expanded(tv, mock_http_from_disk, renewable_rental_expanded):
    sms_list = tv.sms.list(data=renewable_rental_expanded)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_nonrenewable_rental_compact(tv, mock_http_from_disk, nonrenewable_rental_compact):
    sms_list = tv.sms.list(data=nonrenewable_rental_compact)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_nonrenewable_rental_expanded(tv, mock_http_from_disk, nonrenewable_rental_expanded):
    sms_list = tv.sms.list(data=nonrenewable_rental_expanded)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_verification_compact(tv, mock_http_from_disk, verification_compact):
    sms_list = tv.sms.list(data=verification_compact)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


def test_list_sms_by_verification_expanded(tv, mock_http_from_disk, verification_expanded):
    sms_list = tv.sms.list(data=verification_expanded)

    sms_messages = [x.to_api() for x in sms_list]
    assert all(
        dict_subset(sms_test, sms_truth) is None
        for sms_test, sms_truth in zip(sms_messages, mock_http_from_disk.last_response["data"])
    )


@patch("time.sleep")
@patch("time.monotonic")
def test_incoming_sms_timeout(mock_monotonic, mock_sleep, tv, mock_http_from_disk):
    # Mock time.monotonic to simulate timeout
    mock_monotonic.side_effect = [0, 5, 11]  # Start, during, timeout

    sms_iterator = tv.sms.incoming(timeout=10.0, polling_interval=1.0)
    sms_messages = list(sms_iterator)

    # Should return empty list due to timeout
    assert len(sms_messages) == 0


@patch("time.sleep")
def test_incoming_sms_with_messages(mock_sleep, tv, mock_http_from_disk):
    mock_sleep.side_effect = lambda x: 0  # Sleep skips to ensure fast test execution

    # Create mock SMS message that appears to be new
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=1)
    mock_sms = Sms(
        id="sms_123",
        from_value="+1234567890",
        to_value="+0987654321",
        created_at=future_time,
        sms_content="Test message",
        parsed_code=None,
        encrypted=False,
    )

    # Mock the list_sms method to return our test message
    original_list_sms = tv.sms.list
    call_count = 0

    def mock_list_sms(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        print(f"Mock list_sms called {call_count} times")
        if call_count >= 2:  # Return message on second call
            return [mock_sms]
        return []

    sms = tv.sms
    sms.list = mock_list_sms

    try:
        sms_iterator = sms.incoming(timeout=0.05, polling_interval=1.0)
        sms_messages = list(sms_iterator)
        assert len(sms_messages) == 1
        assert sms_messages[0].id == "sms_123"
    finally:
        # Restore original method
        tv.sms.list_sms = original_list_sms


def test_send_sms_with_kwargs(tv, mock_http_from_disk):
    """Test sending SMS using keyword arguments."""
    reservation_id = "renewable_123"
    send_to = "1234567890"
    content = "Test SMS message"

    result = tv.sms.send(reservation_id=reservation_id, send_to=send_to, content=content)

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == reservation_id
    assert mock_http_from_disk.last_body_params["sendTo"] == send_to
    assert mock_http_from_disk.last_body_params["content"] == content


def test_send_sms_with_data_object(tv, mock_http_from_disk):
    """Test sending SMS using SendSmsRequest data object."""
    send_request = SendSmsRequest(reservation_id="renewable_456", send_to="9876543210", content="SMS via data object")

    result = tv.sms.send(data=send_request)

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == "renewable_456"
    assert mock_http_from_disk.last_body_params["sendTo"] == "9876543210"
    assert mock_http_from_disk.last_body_params["content"] == "SMS via data object"


def test_send_sms_with_renewable_rental_compact_instance(tv, mock_http_from_disk, renewable_rental_compact):
    """Test sending SMS using RenewableRentalCompact instance as reservation_id."""
    result = tv.sms.send(reservation_id=renewable_rental_compact, send_to="5551234567", content="Test with instance")

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == renewable_rental_compact.id
    assert mock_http_from_disk.last_body_params["sendTo"] == "5551234567"
    assert mock_http_from_disk.last_body_params["content"] == "Test with instance"


def test_send_sms_with_renewable_rental_expanded_instance(tv, mock_http_from_disk, renewable_rental_expanded):
    """Test sending SMS using RenewableRentalExpanded instance as reservation_id."""
    result = tv.sms.send(reservation_id=renewable_rental_expanded, send_to="5559876543", content="Test expanded")

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == renewable_rental_expanded.id
    assert mock_http_from_disk.last_body_params["sendTo"] == "5559876543"
    assert mock_http_from_disk.last_body_params["content"] == "Test expanded"


def test_send_sms_with_nonrenewable_rental_compact_instance(tv, mock_http_from_disk, nonrenewable_rental_compact):
    """Test sending SMS using NonrenewableRentalCompact instance as reservation_id."""
    result = tv.sms.send(reservation_id=nonrenewable_rental_compact, send_to="5551112222", content="Test nonrenewable compact")

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == nonrenewable_rental_compact.id
    assert mock_http_from_disk.last_body_params["sendTo"] == "5551112222"
    assert mock_http_from_disk.last_body_params["content"] == "Test nonrenewable compact"


def test_send_sms_with_nonrenewable_rental_expanded_instance(tv, mock_http_from_disk, nonrenewable_rental_expanded):
    """Test sending SMS using NonrenewableRentalExpanded instance as reservation_id."""
    result = tv.sms.send(reservation_id=nonrenewable_rental_expanded, send_to="5553334444", content="Test nonrenewable expanded")

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == nonrenewable_rental_expanded.id
    assert mock_http_from_disk.last_body_params["sendTo"] == "5553334444"
    assert mock_http_from_disk.last_body_params["content"] == "Test nonrenewable expanded"


def test_send_sms_kwargs_override_data_object(tv, mock_http_from_disk):
    """Test that kwargs override values in data object."""
    send_request = SendSmsRequest(
        reservation_id="original_reservation", send_to="1111111111", content="Original content"
    )

    result = tv.sms.send(
        data=send_request, reservation_id="override_reservation", send_to="2222222222", content="Override content"
    )

    assert result is True
    assert mock_http_from_disk.last_body_params["reservationId"] == "override_reservation"
    assert mock_http_from_disk.last_body_params["sendTo"] == "2222222222"
    assert mock_http_from_disk.last_body_params["content"] == "Override content"


def test_send_sms_validation_errors(tv, mock_http_from_disk):
    """Test that send method validates required fields."""
    # Test invalid reservation_id
    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="", send_to="1234567890", content="Test")

    with pytest.raises(ValueError):
        tv.sms.send(reservation_id=None, send_to="1234567890", content="Test")

    # Test invalid send_to
    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="valid_id", send_to="", content="Test")

    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="valid_id", send_to="abc123", content="Test")

    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="valid_id", send_to="+1234567890", content="Test")

    # Test missing content
    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="valid_id", send_to="1234567890", content="")

    with pytest.raises(ValueError):
        tv.sms.send(reservation_id="valid_id", send_to="1234567890", content=None)


def test_reply_sms_with_kwargs(tv, mock_http_from_disk):
    """Test replying to SMS using keyword arguments."""
    reply_to_sms_id = "sms_123"
    content = "This is a reply message"

    result = tv.sms.reply(reply_to_sms_id=reply_to_sms_id, content=content)

    assert result is True
    assert mock_http_from_disk.last_body_params["replyToSmsId"] == reply_to_sms_id
    assert mock_http_from_disk.last_body_params["content"] == content


def test_reply_sms_with_data_object(tv, mock_http_from_disk):
    """Test replying to SMS using ReplySmsRequest data object."""
    reply_request = ReplySmsRequest(reply_to_sms_id="sms_456", content="Reply via data object")

    result = tv.sms.reply(data=reply_request)

    assert result is True
    assert mock_http_from_disk.last_body_params["replyToSmsId"] == "sms_456"
    assert mock_http_from_disk.last_body_params["content"] == "Reply via data object"


def test_reply_sms_with_sms_instance(tv, mock_http_from_disk):
    """Test replying to SMS using Sms instance as reply_to_sms_id."""
    test_sms = Sms(
        id="sms_instance_test",
        from_value="+1234567890",
        to_value="+0987654321",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        sms_content="Original message",
        parsed_code=None,
        encrypted=False,
    )

    result = tv.sms.reply(reply_to_sms_id=test_sms, content="Reply to instance")

    assert result is True
    assert mock_http_from_disk.last_body_params["replyToSmsId"] == "sms_instance_test"
    assert mock_http_from_disk.last_body_params["content"] == "Reply to instance"


def test_reply_sms_kwargs_override_data_object(tv, mock_http_from_disk):
    """Test that kwargs override values in data object."""
    reply_request = ReplySmsRequest(reply_to_sms_id="original_sms_id", content="Original reply")

    result = tv.sms.reply(data=reply_request, reply_to_sms_id="override_sms_id", content="Override reply")

    assert result is True
    assert mock_http_from_disk.last_body_params["replyToSmsId"] == "override_sms_id"
    assert mock_http_from_disk.last_body_params["content"] == "Override reply"


def test_reply_sms_validation_errors(tv, mock_http_from_disk):
    """Test that reply method validates required fields."""
    # Test invalid reply_to_sms_id
    with pytest.raises(ValueError):
        tv.sms.reply(reply_to_sms_id="", content="Test reply")

    with pytest.raises(ValueError):
        tv.sms.reply(reply_to_sms_id=None, content="Test reply")

    # Test missing content
    with pytest.raises(ValueError):
        tv.sms.reply(reply_to_sms_id="valid_sms_id", content="")

    with pytest.raises(ValueError):
        tv.sms.reply(reply_to_sms_id="valid_sms_id", content=None)
