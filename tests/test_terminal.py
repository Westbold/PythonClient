"""Terminal commands exercised through SDK-generated HTTP fixtures."""
import io
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

pytest.importorskip("rich")
from rich.console import Console
import textverified as tv
from textverified.terminal import cli, credentials
from .fixtures import mock_http_from_disk, verification_expanded


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    for name in list(os.environ):
        if name.startswith(("TEXTVERIFIED_", "TV_")):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TEXTVERIFIED_CONFIG_DIR", str(tmp_path))


@pytest.fixture
def api(mock_http_from_disk, monkeypatch):
    monkeypatch.setenv("TEXTVERIFIED_API_USERNAME", "someone@example.com")
    monkeypatch.setenv("TEXTVERIFIED_API_KEY", "fake-key")
    calls = []

    def prepare(response, method, url, **kwargs):
        calls.append((method.upper(), url, kwargs))
        if method.upper() == "POST" and url.endswith("/api/pub/v2/verifications"):
            service = kwargs["json"]["serviceName"]
            resource = "mock_verification_success" if service == "test_success" else "string"
            return {"method": "GET", "href": f"https://www.textverified.com/api/pub/v2/verifications/{resource}"}
        if "endsAt" in response:
            response["endsAt"] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
            if url.endswith("mock_verification_success"):
                response["id"] = "mock_verification_success"
        if url.endswith("/sms"):
            for message in response["data"]:
                message["parsedCode"] = "001234"
        return response

    mock_http_from_disk.add_hook(prepare)
    return calls


@pytest.mark.parametrize("mock", [False, True])
def test_verification_uses_sdk_catalog_pricing_creation_and_exact_sms_scope(api, capsys, mock):
    args = (["--mock"] if mock else []) + ["verify", "gma", "--yes"]
    assert cli.main(args) == 0
    output = capsys.readouterr().out
    assert "using gmail" in output
    assert output.rstrip().splitlines()[-1] == "001234"
    service = "test_success" if mock else "gmail"
    pricing = [kwargs for method, url, kwargs in api if url.endswith("/pricing/verifications")]
    assert pricing[0]["json"] == {
        "serviceName": service,
        "areaCode": False,
        "carrier": False,
        "numberType": "mobile",
        "capability": "sms",
    }
    purchases = [
        kwargs for method, url, kwargs in api if method == "POST" and url.endswith("/api/pub/v2/verifications")
    ]
    assert len(purchases) == 1
    assert purchases[0]["json"]["serviceName"] == service
    assert purchases[0]["json"]["maxPrice"] == 5.0
    catalog = [kwargs for method, url, kwargs in api if url.endswith("/services")]
    assert catalog[0]["params"] == {"numberType": "mobile", "reservationType": "verification"}
    sms = [kwargs for method, url, kwargs in api if url.endswith("/sms")]
    assert sms[0]["params"] == {
        "reservationId": "mock_verification_success" if mock else "string",
        "reservationType": "verification",
    }
    assert all(kwargs["timeout"] == 15 for _, _, kwargs in api)
    assert all(
        kwargs["headers"]["User-Agent"] == f"TextVerified-Python-TUI/{tv.__version__}"
        for _, _, kwargs in api
        if "Authorization" in kwargs["headers"]
    )


@pytest.mark.parametrize("mock", [False, True])
def test_catalog_is_identical_with_mock_flag(api, capsys, mock):
    assert cli.main((["--mock"] if mock else []) + ["services", "gmail"]) == 0
    assert "gmail" in capsys.readouterr().out


def test_confirmation_required_before_creation(api, capsys):
    assert cli.main(["verify", "gmail"]) == 2
    assert "pass --yes" in capsys.readouterr().err
    assert not any(method == "POST" and url.endswith("/api/pub/v2/verifications") for method, url, _ in api)


def test_unknown_service_suggests_api_names(api, capsys):
    assert cli.main(["--mock", "verify", "gmal"]) == 1
    assert "Did you mean gmail?" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--demo", "--test-mode"])
def test_removed_flags_are_rejected(flag):
    with pytest.raises(SystemExit) as error:
        cli.main([flag])
    assert error.value.code == 2


def test_mock_requires_credentials(capsys):
    assert cli.main(["--mock", "verify", "gmail", "--yes"]) == 1
    assert "tv login" in capsys.readouterr().err


@pytest.mark.parametrize(
    "allowed, fails, answers, stops, cancelled",
    [
        (True, False, ["y"], True, True),
        (True, False, ["n"], False, False),
        (False, False, [""], False, False),
        (False, False, ["l"], True, False),
        (True, True, ["y", "w"], False, True),
    ],
)
def test_cancel_paths(monkeypatch, verification_expanded, allowed, fails, answers, stops, cancelled):
    order = replace(verification_expanded, cancel=tv.CancelAction(can_cancel=allowed))
    client = Mock()
    client.verifications.details.return_value = order
    if fails:
        client.verifications.cancel.side_effect = tv.TextVerifiedError("CannotCancel", "Cannot cancel now.")
    replies = iter(answers)
    monkeypatch.setattr(cli.console, "input", lambda prompt: next(replies))
    assert cli._confirm_cancel(client, order) is stops
    assert client.verifications.cancel.called is cancelled


def test_interactive_wait_renders_sdk_sms_code(api, monkeypatch):
    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=True, width=80, color_system=None))
    monkeypatch.setattr(cli, "copy_osc52", lambda value: False)
    monkeypatch.setattr(cli, "ANIMATE", False)
    client = cli._client(mock=True)
    try:
        order = client.verifications.details("mock_verification_success")
        assert cli._wait_live(client, order) == 0
    finally:
        client.session.close()
    assert "verified" in output.getvalue()
    assert "0 0 1 2 3 4" in output.getvalue()
    assert "\u2588" in output.getvalue()
    assert "\x1b_G" not in output.getvalue()


def test_login_validates_before_saving(monkeypatch):
    client = Mock()
    client.account.me.return_value = Mock(username="new@example.com", current_balance=10)
    monkeypatch.setattr(cli, "_client", lambda **kw: client)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "new-key")
    assert cli.main(["--mock", "login", "--email", "new@example.com"]) == 0
    assert credentials.load() == (("new@example.com", "new-key"), "cache")
    client.account.me.side_effect = tv.TextVerifiedError("Unauthorized", "Invalid key")
    assert cli.main(["login", "--email", "other@example.com"]) == 1
    assert credentials.load() == (("new@example.com", "new-key"), "cache")
    assert client.session.close.call_count == 2


def test_api_errors_show_description_without_http_trace(api, monkeypatch, capsys):
    client = Mock()
    client.account.me.side_effect = tv.TextVerifiedError("Unauthorized", "Invalid key", "HTTP debug trace")
    monkeypatch.setattr(cli, "_client", lambda **kw: client)
    assert cli.main(["balance"]) == 1
    assert "Invalid key" in capsys.readouterr().err
    assert "HTTP debug trace" not in capsys.readouterr().out
    client.session.close.assert_called_once()


def test_signed_out_home_screen_points_to_login(capsys):
    assert cli.main([]) == 0
    assert "not signed in" in capsys.readouterr().out


def test_signed_out_commands_point_to_login(capsys):
    assert cli.main(["balance"]) == 1
    assert "tv login" in capsys.readouterr().err


def test_logout_without_saved_credentials(capsys):
    assert cli.main(["logout"]) == 0
    assert "No saved credentials" in capsys.readouterr().out


def test_save_load_clear(isolated):
    assert credentials.load() == (None, None)
    credentials.save("someone@example.com", "k-123")
    assert credentials.load() == (("someone@example.com", "k-123"), "cache")
    assert credentials.clear() is True
    assert credentials.load() == (None, None)
    assert not credentials.cache_path().exists()
    assert credentials.clear() is False


def test_environment_wins_over_the_keyring(monkeypatch):
    credentials.save("saved@example.com", "k-saved")
    monkeypatch.setenv("TEXTVERIFIED_API_USERNAME", "env@example.com")
    monkeypatch.setenv("TEXTVERIFIED_API_KEY", "k-env")
    assert credentials.load() == (("env@example.com", "k-env"), "environment")


def test_saving_again_replaces_the_previous_account():
    credentials.save("first@example.com", "k-1")
    credentials.save("second@example.com", "k-2")
    assert credentials.load() == (("second@example.com", "k-2"), "cache")


@pytest.mark.parametrize("geometry_name,rows,columns", [("BLOCKY", 9, 13), ("FINE", 5, 9)])
def test_unicode_badge_frames_keep_designer_geometry(monkeypatch, geometry_name, rows, columns):
    from textverified.terminal import brand

    monkeypatch.setattr(brand, "GEOMETRY", getattr(brand, geometry_name))
    frames = [brand.badge(), brand.waiting_still(), brand.stopped()]
    frames += [brand.dancing(i / 10) for i in range(20)]
    frames += [brand.settling(i / 10) for i in range(11)]
    for frame in frames:
        assert not frame.plain.isascii()
        assert len(frame.plain.splitlines()) == rows
        assert {len(line) for line in frame.plain.splitlines()} == {columns}
    assert brand.settling(1).plain == brand.badge().plain
    assert len({brand.dancing(i / 10).plain for i in range(20)}) > 1


def test_partial_environment_does_not_mix_with_cached_key(monkeypatch):
    credentials.save("saved@example.com", "saved-key")
    monkeypatch.setenv("TEXTVERIFIED_API_USERNAME", "different@example.com")
    with pytest.raises(credentials.CredentialError, match="both"):
        credentials.load()


def test_sdk_import_does_not_load_optional_dependencies():
    import subprocess, sys

    code = (
        "import sys, textverified; assert 'rich' not in sys.modules; assert 'textverified.terminal' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_inline_mark_preserves_logo_checkmark_and_animates():
    from textverified.terminal import brand

    assert brand.inline_mark() == "\u2804\u2840\u2804\u2802"
    frames = {brand.inline_mark(i / 20) for i in range(20)}
    assert len(frames) > 1
    assert all(len(frame) == 4 for frame in frames)
