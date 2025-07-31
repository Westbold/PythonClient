import pytest
from .fixtures import tv, mock_http_from_disk, mock_http
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import Account
import datetime


def test_account_get(tv, mock_http_from_disk):
    account_obj = tv.account.me()
    assert isinstance(account_obj, Account)

    # Make sure we match the expected account details
    assert account_obj.to_api() == mock_http_from_disk.last_response


def test_account_balance(tv, mock_http_from_disk):
    balance = tv.account.balance

    assert isinstance(balance, float)
    assert balance == mock_http_from_disk.last_response.get("currentBalance")


def test_account_username(tv, mock_http_from_disk):
    username = tv.account.username
    assert isinstance(username, str)

    # Make sure we match the expected username
    assert username == mock_http_from_disk.last_response.get("username")
