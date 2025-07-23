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
