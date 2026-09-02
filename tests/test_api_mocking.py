import inspect

import pytest
import textverified

from .fixtures import mock_http_from_disk, tv
from textverified import (
    LIVE,
    MOCK_INSUFFICIENT_BALANCE,
    MOCK_NO_NUMBERS,
    MOCK_PENDING,
    MOCK_SUCCESS,
    TestMode,
    TextVerified,
)
from textverified.action import _Action
from textverified.reservations_api import ReservationsAPI
from textverified.services_api import ServicesAPI
from textverified.verifications_api import VerificationsAPI


@pytest.fixture(autouse=True)
def reset_test_mode():
    textverified.test_mode = LIVE
    yield
    textverified.test_mode = LIVE


def test_test_mode_is_live_by_default():
    assert textverified.test_mode is LIVE


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
@pytest.mark.parametrize(
    ("mode", "service_name"),
    [
        (MOCK_SUCCESS, "test_success"),
        (MOCK_INSUFFICIENT_BALANCE, "test_insufficient_balance"),
    ],
)
def test_global_test_mode_replaces_service_name(tv, mock_http_from_disk, href, mode, service_name):
    textverified.test_mode = mode
    request_body = {"serviceName": "gmail"}

    tv._perform_action(_Action(method="POST", href=href), json=request_body)

    assert mock_http_from_disk.last_body_params == {"serviceName": service_name}
    assert request_body == {"serviceName": "gmail"}


def test_client_test_mode_replaces_service_name(tv, mock_http_from_disk):
    tv.test_mode = MOCK_NO_NUMBERS

    tv._perform_action(_Action(method="POST", href="/api/pub/v2/verifications"), json={"serviceName": "gmail"})

    assert mock_http_from_disk.last_body_params == {"serviceName": "test_no_numbers"}


def test_constructor_accepts_test_mode():
    client = TextVerified(api_key="test-key", api_username="test-user", test_mode=MOCK_PENDING)

    assert client.test_mode is MOCK_PENDING


def test_method_test_mode_has_highest_precedence(tv, mock_http_from_disk):
    textverified.test_mode = MOCK_SUCCESS
    tv.test_mode = MOCK_NO_NUMBERS

    tv._perform_action(
        _Action(method="POST", href="/api/pub/v2/verifications"),
        json={"serviceName": "gmail"},
        test=MOCK_INSUFFICIENT_BALANCE,
    )

    assert mock_http_from_disk.last_body_params == {"serviceName": "test_insufficient_balance"}


def test_test_none_inherits_testing_for_one_method(tv, mock_http_from_disk):
    textverified.test_mode = MOCK_SUCCESS
    tv.test_mode = MOCK_NO_NUMBERS

    tv._perform_action(
        _Action(method="POST", href="/api/pub/v2/verifications"), json={"serviceName": "gmail"}, test=None
    )

    assert mock_http_from_disk.last_body_params == {"serviceName": "test_no_numbers"}


def test_live_overrides_an_inherited_test_mode(tv, mock_http_from_disk):
    textverified.test_mode = MOCK_SUCCESS
    tv.test_mode = MOCK_NO_NUMBERS

    tv._perform_action(
        _Action(method="POST", href="/api/pub/v2/verifications"), json={"serviceName": "gmail"}, test=LIVE
    )

    assert mock_http_from_disk.last_body_params == {"serviceName": "gmail"}


def test_client_live_overrides_global_test_mode(tv, mock_http_from_disk):
    textverified.test_mode = MOCK_SUCCESS
    tv.test_mode = LIVE

    tv._perform_action(_Action(method="POST", href="/api/pub/v2/verifications"), json={"serviceName": "gmail"})

    assert mock_http_from_disk.last_body_params == {"serviceName": "gmail"}


@pytest.mark.parametrize(
    "method",
    [
        VerificationsAPI.create,
        VerificationsAPI.pricing,
        ReservationsAPI.create,
        ReservationsAPI.pricing,
        ServicesAPI.rental_inventory,
        ServicesAPI.verification_inventory,
    ],
)
def test_every_service_name_method_accepts_test_mode(method):
    assert "test" in inspect.signature(method).parameters


def test_set_test_mode_rejects_non_enum_values():
    with pytest.raises(ValueError):
        textverified.set_test_mode("test_success")


def test_all_documented_server_test_modes_are_available():
    assert {mode.value for mode in TestMode} == {
        "live",
        "test_success",
        "test_renewable_expired",
        "test_nonrenewable_expired",
        "test_delayed_success",
        "test_pending",
        "test_insufficient_balance",
        "test_no_numbers",
        "test_too_many_unfinished_verifications",
        "test_timeout",
        "test_reactivatable",
        "test_backorder",
    }
