import pytest
from .fixtures import tv, tv_raw, mock_http_from_disk, mock_http
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.exceptions import TextVerifiedError
import datetime


def test_bearer_get(tv_raw, mock_http_from_disk):
    tv_raw.refresh_bearer()

    assert isinstance(tv_raw.bearer, BearerToken)
    assert not tv_raw.bearer.is_expired()
    mock_http_from_disk.assert_called_once_with(
        "POST",
        "https://www.textverified.com/api/pub/v2/auth",
        data=None,
        json=None,
        headers={"X-API-KEY": "test-key", "X-API-USERNAME": "test-user"},
        verify=True,
    )


def test_expired_bearer_refreshed(tv_raw, mock_http_from_disk):
    tv_raw.bearer = BearerToken(
        token="expired-token",
        expires_at=datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=1),
    )

    assert tv_raw.bearer.is_expired()
    tv_raw.refresh_bearer()
    assert not tv_raw.bearer.is_expired()
    mock_http_from_disk.assert_called_once_with(
        "POST",
        "https://www.textverified.com/api/pub/v2/auth",
        data=None,
        json=None,
        verify=True,
        headers={"X-API-KEY": "test-key", "X-API-USERNAME": "test-user"},
    )


def test_valid_bearer_not_refreshed(tv, mock_http_from_disk):
    tv.bearer = BearerToken(
        token="valid-token",
        expires_at=datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=3600),
    )

    assert not tv.bearer.is_expired()
    tv.refresh_bearer()
    assert not tv.bearer.is_expired()
    mock_http_from_disk.assert_not_called()


def test_api_performs_action(tv, mock_http_from_disk):
    action = _Action(method="GET", href="/api/pub/v2/fake-endpoint")
    tv._perform_action(action)


def test_refresh_bearer_before_action(tv, mock_http_from_disk):
    # Ensure bearer is refreshed before performing an action
    tv.bearer = BearerToken(
        token="expired-token",
        expires_at=datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=1),
    )

    assert tv.bearer.is_expired()
    tv._perform_action(_Action(method="GET", href="/api/pub/v2/fake-endpoint"))
    assert not tv.bearer.is_expired()


def test_no_leak_external_request(tv, mock_http):
    # If we request to something that isn't base_url, it doesn't leak the bearer token
    mock_http.return_value.status_code = 200
    action = _Action(method="GET", href="https://www.example.com/api/pub/v2/external-endpoint")

    tv._perform_action(action)

    mock_http.assert_called_once_with(
        method="GET",
        url="https://www.example.com/api/pub/v2/external-endpoint",
        headers={"User-Agent": tv.user_agent},
        verify=True,
    )


def test_error_on_status_code_400(tv, mock_http):
    mock_http.return_value.status_code = 400
    mock_http.return_value.json.return_value = {
        "errorCode": "TooManyUnfinishedVerifications",
        "errorDescription": "Too many pending verifications.",
    }

    action = _Action(method="POST", href="/api/pub/v2/verifications")

    with pytest.raises(TextVerifiedError) as exc_info:
        tv._perform_action(action)

    # Assert the exception details
    assert exc_info.value.error_code == "TooManyUnfinishedVerifications"
    assert exc_info.value.error_description == "Too many pending verifications."
    assert "400" in exc_info.value.context
    assert "/api/pub/v2/verifications" in exc_info.value.context
    assert "POST" in exc_info.value.context

    mock_http.assert_called_once_with(
        method="POST",
        url=f"{tv.base_url}/api/pub/v2/verifications",
        headers={"Authorization": f"Bearer {tv.bearer.token}", "User-Agent": tv.user_agent},
        verify=True,
    )
