import textverified
import pytest

from .fixtures import tv, mock_http_from_disk
from textverified.action import _Action
from textverified import TextVerified


def test_mock_api_is_disabled_by_default():
    assert textverified.mock_api is False


@pytest.mark.parametrize(
    "href",
    [
        "/api/pub/v2/verifications",
        "/api/pub/v2/reservations/rental",
        "/api/pub/v2/pricing/verifications",
        "/api/pub/v2/pricing/rentals",
        "/api/pub/v2/inventory/verifications",
        "/api/pub/v2/inventory/rentals",
    ],
)
def test_mock_api_flag_replaces_service_name_on_supported_request(tv, mock_http_from_disk, href):
    request_body = {"serviceName": "gmail"}
    textverified.set_mock_api(True)
    try:
        tv._perform_action(_Action(method="POST", href=href), json=request_body)
    finally:
        textverified.set_mock_api(False)

    assert mock_http_from_disk.last_body_params == {"serviceName": "test_success"}
    assert "x-phoneblur-mock" not in mock_http_from_disk.last_header_params
    assert request_body == {"serviceName": "gmail"}


def test_mock_api_flag_does_not_modify_unsupported_request(tv, mock_http_from_disk):
    textverified.set_mock_api(True)
    try:
        tv._perform_action(_Action(method="POST", href="/api/pub/v2/sms/send"), json={"serviceName": "gmail"})
    finally:
        textverified.set_mock_api(False)

    assert mock_http_from_disk.last_body_params == {"serviceName": "gmail"}


def test_set_mock_api_requires_bool():
    try:
        textverified.set_mock_api("true")
    except ValueError:
        pass
    else:
        raise AssertionError("set_mock_api should reject non-boolean values")


def test_client_mock_api_flag_replaces_service_name(tv, mock_http_from_disk):
    tv.mock_api = True
    tv._perform_action(_Action(method="POST", href="/api/pub/v2/verifications"), json={"serviceName": "gmail"})

    assert mock_http_from_disk.last_body_params == {"serviceName": "test_success"}


def test_constructor_accepts_mock_api_flag():
    client = TextVerified(api_key="test-key", api_username="test-user", mock_api=True)

    assert client.mock_api is True
