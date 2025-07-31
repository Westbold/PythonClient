import pytest
from unittest.mock import patch, MagicMock
from .fixtures import (
    tv,
    mock_http_from_disk,
    mock_http,
    dict_subset,
    renewable_rental_compact,
    nonrenewable_rental_compact,
)
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    RenewableRentalCompact,
    RenewableRentalExpanded,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    WakeRequest,
    WakeResponse,
    UsageWindowEstimateRequest,
)
import datetime


def create_move_action_hook(nmethod, href):
    def move_action_to_endpoint(response, method, url, **kwargs):
        if "href" in response and "method" in response:
            response["href"] = href
            response["method"] = nmethod
        return response

    return move_action_to_endpoint


def test_create_wake_request_by_id(tv, mock_http_from_disk):
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    reservation_id = "string"
    wake_response = tv.wake_requests.create(reservation_id)

    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None


def test_create_wake_request_by_renewable_instance(tv, mock_http_from_disk, renewable_rental_compact):
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    wake_response = tv.wake_requests.create(renewable_rental_compact)

    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None


def test_create_wake_request_by_nonrenewable_instance(tv, mock_http_from_disk, nonrenewable_rental_compact):
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    wake_response = tv.wake_requests.create(nonrenewable_rental_compact)

    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None


def test_get_wake_request_by_id(tv, mock_http_from_disk):
    wake_request_id = "string"
    wake_response = tv.wake_requests.get(wake_request_id)

    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None
    assert wake_response.id == wake_request_id


def test_get_wake_request_by_instance(tv, mock_http_from_disk):
    test_get_wake_request_by_id(tv, mock_http_from_disk)  # Load the wake request
    wake_request = WakeResponse.from_api(mock_http_from_disk.last_response)

    wake_response = tv.wake_requests.get(wake_request)

    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None


def test_estimate_usage_window_by_id(tv, mock_http_from_disk):
    reservation_id = "string"
    usage_estimate = tv.wake_requests.estimate_usage_window(reservation_id)

    assert isinstance(usage_estimate, UsageWindowEstimateRequest)
    assert dict_subset(usage_estimate.to_api(), mock_http_from_disk.last_response) is None


def test_estimate_usage_window_by_renewable_instance(tv, mock_http_from_disk, renewable_rental_compact):
    usage_estimate = tv.wake_requests.estimate_usage_window(renewable_rental_compact)

    assert isinstance(usage_estimate, UsageWindowEstimateRequest)
    assert dict_subset(usage_estimate.to_api(), mock_http_from_disk.last_response) is None


def test_estimate_usage_window_by_nonrenewable_instance(tv, mock_http_from_disk, nonrenewable_rental_compact):
    usage_estimate = tv.wake_requests.estimate_usage_window(nonrenewable_rental_compact)

    assert isinstance(usage_estimate, UsageWindowEstimateRequest)
    assert dict_subset(usage_estimate.to_api(), mock_http_from_disk.last_response) is None


@patch("time.sleep")
def test_wait_for_wake_request_by_id(mock_sleep, tv, mock_http_from_disk):
    mock_sleep.side_effect = lambda x: 0  # Skip actual sleep for fast test execution

    # Create a mock wake response with scheduled time in the past (ready to wake)
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    # Mock the get_wake_request call to return a scheduled wake request
    wake_requests = tv.wake_requests

    def mock_get_wake_request(wake_request_id):
        return WakeResponse(
            id=wake_request_id,
            usage_window_start=past_time,
            usage_window_end=future_time,
            is_scheduled=True,
            reservation_id="string",
        )

    wake_requests.get = mock_get_wake_request

    wake_request_id = "string"
    result = wake_requests.wait_for_wake_request(wake_request_id)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


@patch("time.sleep")
def test_wait_for_wake_request_by_instance(mock_sleep, tv, mock_http_from_disk):
    mock_sleep.side_effect = lambda x: 0  # Skip actual sleep for fast test execution

    # Create a scheduled wake response
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    wake_response = WakeResponse(
        id="string",
        usage_window_start=past_time,
        usage_window_end=future_time,
        is_scheduled=True,
        reservation_id="string",
    )

    result = tv.wake_requests.wait_for_wake_request(wake_response)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


@patch("time.sleep")
def test_wait_for_wake_request_future_window(mock_sleep, tv, mock_http_from_disk):
    """Test waiting for a wake request with future usage window."""
    mock_sleep.side_effect = lambda x: 0  # Skip sleep
    wake_requests = tv.wake_requests

    # Create a wake response with usage window starting in 2 seconds
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_start = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=2)
    future_end = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    wake_response = WakeResponse(
        id="string",
        usage_window_start=future_start,
        usage_window_end=future_end,
        is_scheduled=True,
        reservation_id="string",
    )

    # The function call will request an updated usage window
    # this usage window will be in the present

    def mock_get_wake_request(wake_request_id):
        return WakeResponse(
            id=wake_request_id,
            usage_window_start=past_time,
            usage_window_end=future_end,
            is_scheduled=True,
            reservation_id="string",
        )

    wake_requests.get = mock_get_wake_request

    # Test the wait function
    result = wake_requests.wait_for_wake_request(wake_response)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


def test_wait_for_wake_request_invalid_id(tv, mock_http_from_disk):
    """Test error handling for invalid wake request ID."""
    with pytest.raises(ValueError, match="wake_request_id must be a valid ID or instance of WakeResponse"):
        tv.wake_requests.wait_for_wake_request(None)


def test_wait_for_wake_request_not_scheduled(tv, mock_http_from_disk):
    """Test error handling for unscheduled wake request."""
    wake_response = WakeResponse(
        id="string", usage_window_start=None, usage_window_end=None, is_scheduled=False, reservation_id="string"
    )

    with pytest.raises(ValueError, match="Wake request must be scheduled with a valid usage window"):
        tv.wake_requests.wait_for_wake_request(wake_response)


@patch("time.sleep")
def test_wait_for_number_wake_by_id(mock_sleep, tv, mock_http_from_disk):
    """Test waiting for number wake using reservation ID."""
    mock_sleep.side_effect = lambda x: 0  # Skip actual sleep for fast test execution

    # Mock create_wake_request hook to redirect
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    # Mock the wake response to be scheduled and ready
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    wake_requests = tv.wake_requests

    def mock_create_wake_request(reservation_id):
        return WakeResponse(
            id="wake_string",
            usage_window_start=past_time,
            usage_window_end=future_time,
            is_scheduled=True,
            reservation_id=reservation_id if isinstance(reservation_id, str) else reservation_id.id,
        )

    wake_requests.create = mock_create_wake_request

    reservation_id = "string"
    result = wake_requests.wait_for_number_wake(reservation_id)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


@patch("time.sleep")
def test_wait_for_number_wake_by_renewable_instance(mock_sleep, tv, mock_http_from_disk, renewable_rental_compact):
    """Test waiting for number wake using renewable rental instance."""
    mock_sleep.side_effect = lambda x: 0  # Skip actual sleep for fast test execution

    # Mock create_wake_request hook
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    # Mock the wake response to be scheduled and ready
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    wake_requests = tv.wake_requests

    def mock_create_wake_request(reservation_id):
        return WakeResponse(
            id="wake_string",
            usage_window_start=past_time,
            usage_window_end=future_time,
            is_scheduled=True,
            reservation_id=reservation_id if isinstance(reservation_id, str) else reservation_id.id,
        )

    wake_requests.create = mock_create_wake_request

    result = wake_requests.wait_for_number_wake(renewable_rental_compact)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


@patch("time.sleep")
def test_wait_for_number_wake_by_nonrenewable_instance(
    mock_sleep, tv, mock_http_from_disk, nonrenewable_rental_compact
):
    """Test waiting for number wake using non-renewable rental instance."""
    mock_sleep.side_effect = lambda x: 0  # Skip actual sleep for fast test execution

    # Mock create_wake_request hook
    mock_http_from_disk.add_hook(
        create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string")
    )

    # Mock the wake response to be scheduled and ready
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)

    wake_requests = tv.wake_requests

    def mock_create_wake_request(reservation_id):
        return WakeResponse(
            id="wake_string",
            usage_window_start=past_time,
            usage_window_end=future_time,
            is_scheduled=True,
            reservation_id=reservation_id if isinstance(reservation_id, str) else reservation_id.id,
        )

    wake_requests.create = mock_create_wake_request

    result = wake_requests.wait_for_number_wake(nonrenewable_rental_compact)

    assert isinstance(result, WakeResponse)
    assert result.is_scheduled is True


def test_wait_for_number_wake_create_failure(tv, mock_http_from_disk):
    """Test error handling when wake request creation fails."""
    wake_requests = tv.wake_requests
    wake_requests.create = lambda x: None

    with pytest.raises(ValueError, match="Failed to create wake request."):
        wake_requests.wait_for_number_wake("string")
