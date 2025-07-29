import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset, renewable_rental_compact, nonrenewable_rental_compact
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.generated.generated_enums import (
    RenewableRentalCompact, RenewableRentalExpanded,
    NonrenewableRentalCompact, NonrenewableRentalExpanded,
    WakeRequest, WakeResponse, UsageWindowEstimateRequest
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
    mock_http_from_disk.add_hook(create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string"))
    
    reservation_id = "string"
    wake_response = tv.wake_requests.create_wake_request(reservation_id)
    
    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None

def test_create_wake_request_by_renewable_instance(tv, mock_http_from_disk, renewable_rental_compact):
    mock_http_from_disk.add_hook(create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string"))
    
    wake_response = tv.wake_requests.create_wake_request(renewable_rental_compact)
    
    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None

def test_create_wake_request_by_nonrenewable_instance(tv, mock_http_from_disk, nonrenewable_rental_compact):
    mock_http_from_disk.add_hook(create_move_action_hook("get", "https://textverified.com/api/pub/v2/wake-requests/wake_string"))
    
    wake_response = tv.wake_requests.create_wake_request(nonrenewable_rental_compact)
    
    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None

def test_get_wake_request_by_id(tv, mock_http_from_disk):
    wake_request_id = "string"
    wake_response = tv.wake_requests.get_wake_request(wake_request_id)
    
    assert isinstance(wake_response, WakeResponse)
    assert dict_subset(wake_response.to_api(), mock_http_from_disk.last_response) is None
    assert wake_response.id == wake_request_id

def test_get_wake_request_by_instance(tv, mock_http_from_disk):
    test_get_wake_request_by_id(tv, mock_http_from_disk)  # Load the wake request
    wake_request = WakeResponse.from_api(mock_http_from_disk.last_response)
    
    wake_response = tv.wake_requests.get_wake_request(wake_request)
    
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