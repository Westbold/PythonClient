"""Terminal behavior tests use fake accounts; no credentials or purchases."""
import asyncio
import copy
import io
import json
import os
import sys
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

pytest.importorskip("typer")
pytest.importorskip("textual")
pytest.importorskip("jsonschema")
from typer.testing import CliRunner
from textverified.action import _Action, _ActionResponse
from textverified.terminal.adapter import Adapter, _iter_api_pages
from textverified.terminal import cli
from textverified.terminal.application import Application
from textverified.terminal.config import Config, TerminalError
from textverified.terminal.fields import validate, merge_inputs, descriptor
from textverified.terminal.models import message_record, number_record, safe, sort_number
from textverified.terminal.output import finite
from textverified.terminal.state import State
from textverified.terminal.sync import Feed


def sms(identity, body="Your code", code=None, created="2026-10-01T01:00:00Z"):
    return message_record(
        dict(id=identity, to="001234", **{"from": "00001"}, createdAt=created, smsContent=body, parsedCode=code)
    )


class FakeAdapter:
    scope = "https://www.textverified.com|fake"
    username = "fake"
    account_scope = dict(profile=None, username="fake", api_origin="https://www.textverified.com")

    def __init__(self):
        self.rows = [sms("external-inactive", code="001234"), sms("unassociated", created="2026-09-01T01:00:00Z")]
        self.resources_data = [
            number_record(dict(id="r", state="renewableActive", number="001234"), "renewable", self.scope),
            number_record(dict(id="v", state="verificationPending", number="987654"), "verification", self.scope),
        ]
        self.submits = 0
        self.resolve_error = False
        self.submit_error = None

    def messages(self, **kwargs):
        yield from copy.deepcopy(self.rows)

    def resources(self, kind="all", cancel=None):
        yield from copy.deepcopy(
            [
                r
                for r in self.resources_data
                if kind == "all" or r["kind"] == kind or kind == "rental" and r["kind"] != "verification"
            ]
        )

    def details(self, kind, identity):
        return copy.deepcopy(next(r for r in self.resources_data if r["resource_id"] == identity))

    def account(self):
        return dict(
            self.account_scope,
            balance_amount="12.50",
            balance_unit="credits",
            fetched_at="2026-10-01T00:00:00Z",
            freshness="fresh",
        )

    def quote(self, kind, request):
        return dict(
            amount="0.95",
            amount_unit=None,
            fetched_at="2026-10-01T00:00:00Z",
            price_protection="server" if kind == "verification" else "preflight_only",
        )

    def submit(self, kind, request):
        self.submits += 1
        if self.submit_error:
            raise self.submit_error
        return {"method": "GET", "href": "/details"}

    def resolve(self, kind, acceptance):
        if self.resolve_error:
            raise OSError("fake follow-up failure")
        return dict(id="new", totalCost=0.95)

    def services(self, kind):
        return ["example", "test"]

    def close(self):
        pass


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("TEXTVERIFIED_CONFIG_DIR", str(tmp_path))
    config = Config()
    value = Application(FakeAdapter(), config, State(config))
    yield value
    value.close()


def test_feed_account_wide_updates_and_late_records(service):
    feed = service.feed
    initial = list(feed.reconcile())
    assert {m["id"] for _, m in initial} == {"external-inactive", "unassociated"}
    assert all(m["resource_id"] is None for _, m in initial)
    assert not list(feed.reconcile())
    service.adapter.rows.extend([sms("same-body-a"), sms("same-body-b"), sms("late", created="2025-01-01T00:00:00Z")])
    events = list(feed.reconcile())
    assert len(events) == 3
    service.adapter.rows[0]["parsed_code"] = "000999"
    assert list(feed.reconcile())[0][0] == "sms.updated"


def test_feed_retains_newest_bodies_in_unspecified_page_order():
    adapter = FakeAdapter()
    adapter.rows = [sms(str(i), created="2026-10-%02dT00:00:00Z" % i) for i in range(1, 20)]
    adapter.rows.reverse()
    feed = Feed(adapter, max_bodies=3)
    assert len(list(feed.reconcile())) == 19
    assert set(feed.messages) == {"17", "18", "19"}
    assert not list(feed.reconcile())


def test_purchase_acceptance_never_resubmits(service):
    request, quote = service.quote("verification", dict(serviceName="example", capability="sms"))
    service.adapter.resolve_error = True
    result = service.buy("verification", request, quote)
    assert result["outcome"] == "accepted" and result["detail_status"] == "pending"
    assert service.adapter.submits == 1
    row = service.state.db.execute("SELECT payload FROM receipts").fetchone()
    assert json.loads(row[0])["outcome"] == "accepted"


def test_purchase_ambiguity_receipt(service):
    import requests

    request, quote = service.quote("verification", dict(serviceName="example", capability="sms"))
    service.adapter.submit_error = requests.ConnectionError("secret-bearing response")
    with pytest.raises(TerminalError) as error:
        service.buy("verification", request, quote)
    assert error.value.status == 9
    assert service.adapter.submits == 1
    assert json.loads(service.state.db.execute("SELECT payload FROM receipts").fetchone()[0])["outcome"] == "unknown"
    assert "secret-bearing" not in str(error.value)


def test_server_price_cap_checked_before_quote(service):
    with pytest.raises(TerminalError) as error:
        service.quote("rental", {}, require_cap=True)
    assert error.value.status == 7
    assert service.adapter.submits == 0


def test_schema_omission_and_explicit_values():
    base = dict(serviceName="example", capability="sms")
    for value in (None, 0, 0.5):
        request = validate("verification.buy", dict(base, maxPrice=value))
        assert request.to_api()["maxPrice"] == value
    assert "maxPrice" not in validate("verification.buy", base).to_api()
    request = validate("verification.buy", dict(base, areaCodeSelectOption=[], serviceNotListedName=""))
    assert request.to_api()["areaCodeSelectOption"] == []
    assert request.to_api()["serviceNotListedName"] == ""
    with pytest.raises(ValueError, match="Conflicting"):
        merge_inputs("verification.buy", [{"serviceName": "a"}, {"service_name": "a"}])
    with pytest.raises(ValueError, match="Unknown"):
        validate("verification.buy", dict(base, made_up=True))


def test_schema_generated_fields_reach_sdk_transport():
    from textverified.terminal.adapter import Adapter

    request = validate(
        "rental.buy",
        dict(
            serviceName="example",
            capability="sms",
            duration="30d",
            isRenewable=False,
            numberType="mobile",
            allowBackOrderReservations=False,
            alwaysOn=None,
            areaCodeSelectOption=[],
            billingCycleIdToAssignTo="",
        ),
    )
    adapter = Adapter("fake", "fake")
    client = adapter.client
    client._perform_action = Mock(return_value=_ActionResponse({}, {}))
    adapter.submit("rental", request)
    assert client._perform_action.call_args.kwargs["json"] == request.to_api()
    assert request.to_api()["isRenewable"] is False


def test_raw_pages_follow_later_page_and_reject_cycles():
    client = SimpleNamespace(
        base_url="https://example.com",
        _perform_action=Mock(
            side_effect=[
                _ActionResponse(dict(data=[1], hasNext=True, links={"next": dict(method="GET", href="/page2")}), {}),
                _ActionResponse(dict(data=[2], hasNext=False), {}),
            ]
        ),
    )
    assert [p["data"] for p in _iter_api_pages(client, _Action("GET", "/page1"))] == [[1], [2]]
    client._perform_action = Mock(
        return_value=_ActionResponse(dict(data=[], hasNext=True, links={"next": dict(method="GET", href="/page1")}), {})
    )
    with pytest.raises(ValueError, match="Cyclic"):
        list(_iter_api_pages(client, _Action("GET", "/page1")))
    with pytest.raises(ValueError, match="Cross-origin"):
        list(_iter_api_pages(client, _Action("GET", "https://evil.example/page")))


def test_finite_json_failure_keeps_stdout_empty(capsys):
    def records():
        yield sms("first")
        raise OSError("fail midway")

    with pytest.raises(OSError):
        finite(records(), {}, format="json", limit=None, sms=True)
    assert capsys.readouterr().out == ""


def test_cli_json_and_search_match_limit(service, monkeypatch):
    monkeypatch.setattr(cli, "workflow", lambda ctx: service)
    service.adapter.rows = [sms("a", body="no match"), sms("b", body="SIGN-IN"), sms("c", body="sign-in")]
    result = CliRunner().invoke(cli.app, ["sms", "list", "--query", "sign-in", "--limit", "1", "--json"])
    assert result.exit_code == 0, result.exception
    output = json.loads(result.stdout)
    assert output["items"][0]["id"] == "b"
    assert output["meta"]["has_more"] is True
    assert "\x1b" not in result.stdout


def test_cli_wait_preserves_code_and_timeout(service, monkeypatch):
    monkeypatch.setattr(cli, "workflow", lambda ctx: service)
    result = CliRunner().invoke(cli.app, ["sms", "wait", "--since", "2026-10-01T00:00:00Z", "--code-only"])
    assert result.exit_code == 0, result.exception
    assert result.stdout == "001234\n"
    result = CliRunner().invoke(cli.app, ["sms", "wait", "--timeout", "0.01"])
    assert isinstance(result.exception, TerminalError) and result.exception.status == 8
    assert result.stdout == ""


def test_cli_watch_tail_zero_silent_baseline(service, monkeypatch):
    monkeypatch.setattr(cli, "workflow", lambda ctx: service)
    result = CliRunner().invoke(cli.app, ["sms", "watch", "--tail", "0", "--timeout", "0.01", "--format", "ndjson"])
    assert result.exit_code == 0, result.exception
    assert result.stdout == ""
    assert "Listening" in result.stderr


def test_credentials_whole_pair_precedence(service, monkeypatch):
    import keyring

    config = service.config
    config.profiles["work"] = dict(api_username="saved-user", credential_ref="textverified/work")
    monkeypatch.setenv("TEXTVERIFIED_API_USERNAME", "env-user")
    monkeypatch.setenv("TEXTVERIFIED_API_KEY", "env-key")
    monkeypatch.setattr(keyring, "get_password", lambda ref, user: "saved-key")
    assert config.credentials("work") == ("saved-user", "saved-key", "work")
    assert config.credentials() == ("env-user", "env-key", None)
    monkeypatch.delenv("TEXTVERIFIED_API_KEY")
    with pytest.raises(TerminalError):
        config.credentials()


def test_unknown_state_and_terminal_safety():
    from textverified.data import ReservationState, ReservationCapability

    with pytest.raises(ValueError):
        ReservationState.from_api("brandNewState")
    with pytest.raises(ValueError):
        ReservationCapability.from_api("brandNewCapability")
    row = number_record(dict(id="v", state="brandNewState"), "verification", "account")
    assert row["lifecycle"] == "attention"
    assert safe("[red]literal[/red]\x1b[31mtext\x1b]52;c;bad\x07") == "[red]literal[/red]text"


def test_tui_views_editable_shortcuts_and_selection(service):
    from textverified.terminal.tui import TerminalApp, Purchase
    from textual.widgets import Input, DataTable, TabbedContent

    async def scenario():
        app = TerminalApp(service, config=service.config)
        async with app.run_test(size=(100, 32)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert app.query_one("#numbers-list", DataTable).row_count == 2
            app.query_one("#numbers-search", Input).focus()
            await pilot.press("v", "r", "q")
            assert app.query_one("#numbers-search", Input).value == "vrq"
            assert not isinstance(app.screen, Purchase)
            await pilot.press("escape", "2")
            await pilot.pause()
            assert app.query_one("#views", TabbedContent).active == "inbox"
            table = app.query_one("#inbox-list", DataTable)
            table.focus()
            await pilot.press("down", "enter")
            identity = app.selected_message
            service.adapter.rows.append(sms("newest", created="2026-10-02T01:00:00Z"))
            app.action_refresh()
            await app.workers.wait_for_complete()
            assert app.selected_message == identity
            assert table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value == identity
            assert app.theme == "textverified-dark"
            (service.config.directory / "terminal.svg").write_text(app.export_screenshot(), encoding="utf-8")

    asyncio.run(scenario())


def test_tui_confirm_defaults_back_and_dispatches_once(service):
    from textverified.terminal.tui import TerminalApp, Confirm

    async def scenario():
        app = TerminalApp(service, config=service.config)
        calls = []

        async def callback():
            calls.append(True)
            await asyncio.sleep(0.01)
            return {"outcome": "created"}

        async with app.run_test(size=(100, 32)) as pilot:
            await pilot.pause()
            app.push_screen(Confirm("Review", callback))
            await pilot.pause()
            assert app.focused.id == "back"
            await pilot.press("tab", "enter", "enter")
            await pilot.pause()
            assert len(calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "operation,field", [(op, f) for op in ("verification.buy", "rental.buy") for f in descriptor(op)["fields"]]
)
def test_each_generated_field_survives_validation_and_sdk_transport(operation, field):
    values = dict(serviceName="example", capability="sms")
    if operation == "rental.buy":
        values.update(duration="thirtyDay", isRenewable=False, numberType="mobile", allowBackOrderReservations=False)
    schema = field["schema"]
    if "enum" in schema:
        value = schema["enum"][0]
    elif schema.get("type") == "boolean":
        value = False
    elif schema.get("type") == "array":
        value = []
    elif schema.get("type") in ("number", "integer"):
        value = 0
    elif schema.get("type") == "object":
        value = {}
    else:
        value = "example"
    values[field["api_field_name"]] = value
    request = validate(operation, values)
    adapter = Adapter("fake", "fake")
    client = adapter.client
    client._perform_action = Mock(return_value=_ActionResponse({}, {}))
    adapter.submit(operation.split(".")[0], request)
    assert client._perform_action.call_args.kwargs["json"][field["api_field_name"]] == value


def test_new_optional_field_is_discoverable_and_transmitted(monkeypatch):
    from textverified.terminal.fields import METADATA

    operation = copy.deepcopy(METADATA["operations"]["verification.buy"])
    operation["fields"].append(
        dict(
            client_field_name="new_option",
            api_field_name="newOption",
            python_field_name="new_option",
            required=False,
            has_default=False,
            schema={"type": "boolean"},
        )
    )
    operation["schema"]["properties"]["newOption"] = {"type": "boolean"}
    monkeypatch.setitem(METADATA["operations"], "verification.buy", operation)
    request = validate("verification.buy", dict(service_name="example", capability="sms", new_option=False))
    adapter = Adapter("fake", "fake")
    client = adapter.client
    client._perform_action = Mock(return_value=_ActionResponse({}, {}))
    adapter.submit("verification", request)
    assert client._perform_action.call_args.kwargs["json"]["newOption"] is False


def test_pinned_schema_metadata_regeneration_is_deterministic(tmp_path):
    from generate_terminal_metadata import generate_terminal_metadata
    from pathlib import Path

    source = json.loads(Path("swagger.json").read_text(encoding="utf-8"))
    path = tmp_path / "fields.json"
    generate_terminal_metadata(source, str(path))
    assert path.read_bytes() == Path("textverified/terminal/fields.json").read_bytes()


def test_read_markers_restore_unread_without_archiving_content(service):
    state = service.state
    assert not state.observe(service.adapter.scope, [sms("historical")], baseline=True)
    assert state.observe(
        service.adapter.scope, [sms("incoming", body="sensitive-body", code="secret-code")], baseline=False
    ) == {"incoming"}
    assert state.observe(service.adapter.scope, [sms("incoming")], baseline=True) == {"incoming"}
    state.mark_read(service.adapter.scope, "incoming")
    assert not state.observe(service.adapter.scope, [sms("incoming")], baseline=False)
    payload = str(state.db.execute("SELECT * FROM messages").fetchall())
    assert "sensitive-body" not in payload and "secret-code" not in payload


@pytest.mark.parametrize("size", [(120, 35), (80, 24), (60, 16), (45, 12)])
def test_tui_resize_and_login_path(service, size):
    from textverified.terminal.tui import TerminalApp, Login
    from textual.widgets import Static

    async def scenario():
        app = TerminalApp(config=service.config)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, Login)
            await pilot.press("tab", "tab", "tab")
            await pilot.pause()
            assert app.focused.id == "login-submit"
            assert 0 <= app.focused.region.y < app.focused.region.bottom <= size[1]
            await pilot.press("escape")
            app.paint_time()
            assert app.query_one("#account-bar", Static).display
            assert app.query_one("#small-terminal", Static).display == (size[0] < 60 or size[1] < 16)

    asyncio.run(scenario())


def test_rental_quote_uses_pinned_always_on_contract(service):
    from textverified.terminal.adapter import Adapter
    from textverified.data import PricingSnapshot

    adapter = Adapter("fake", "fake")
    adapter.client._perform_action = Mock(return_value=_ActionResponse({"price": 1.0, "serviceName": "example"}, {}))
    request = validate(
        "rental.buy",
        dict(
            serviceName="example",
            capability="sms",
            duration="30d",
            isRenewable=False,
            numberType="mobile",
            allowBackOrderReservations=False,
        ),
    )
    assert adapter.quote("rental", request)["amount"] == "1.0"
    assert "alwaysOn" not in request.to_api()
    adapter.close()


def test_tui_profile_generation_discards_old_account_response(service):
    from textverified.terminal.tui import TerminalApp

    async def scenario():
        started, release = threading.Event(), threading.Event()
        old = service.adapter
        original = old.messages

        def slow(**kwargs):
            started.set()
            release.wait(2)
            yield from original(**kwargs)

        old.messages = slow
        app = TerminalApp(service, config=service.config)
        async with app.run_test(size=(100, 32)) as pilot:
            await pilot.pause()
            assert started.is_set()
            new_adapter = FakeAdapter()
            new_adapter.username = "other-account"
            new_adapter.scope = "other-account"
            new_adapter.rows = [sms("other-account-message")]
            other = Application(new_adapter, service.config, State(service.config))
            app.switch_application(other)
            release.set()
            await app.workers.wait_for_complete()
            assert set(app.messages) == {"other-account-message"}
            other.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "kind,args", [("verification", ["--service", "example"]), ("rental", ["--service", "example", "--duration", "30d"])]
)
def test_cli_purchase_quote_and_explicit_buy(service, monkeypatch, kind, args):
    monkeypatch.setattr(cli, "workflow", lambda ctx: service)
    runner = CliRunner()
    quote = runner.invoke(cli.app, [kind, "quote", *args, "--json"])
    assert quote.exit_code == 0, quote.exception
    assert json.loads(quote.stdout)["quote"]["amount"] == "0.95"
    assert service.adapter.submits == 0
    result = runner.invoke(cli.app, [kind, "buy", *args, "--yes", "--json"])
    assert result.exit_code == 0, result.exception
    assert json.loads(result.stdout)["outcome"] == "created"
    assert service.adapter.submits == 1


def test_documented_exact_sms_query_reaches_sdk_and_labels_scope():
    from textverified.terminal.adapter import Adapter

    adapter = Adapter("fake", "fake")
    adapter.client._perform_action = Mock(
        return_value=_ActionResponse(
            dict(
                data=[
                    dict(id="m", to="001234", createdAt="2026-10-01T00:00:00Z", smsContent="code", parsedCode="001234")
                ],
                hasNext=False,
            ),
            {},
        )
    )
    messages = list(adapter.messages(resource_id="verification-id", resource_kind="verification"))
    assert adapter.client._perform_action.call_args.kwargs["params"] == {
        "reservationId": "verification-id",
        "reservationType": "verification",
    }
    assert messages[0]["resource_id"] == "verification-id"
    assert messages[0]["association_source"] == "scoped_query"
    adapter.close()


def test_terminal_user_agent_sent_to_api():
    import datetime
    from requests import Response
    from textverified import __version__
    from textverified.textverified import BearerToken
    from textverified.terminal.adapter import Adapter

    adapter = Adapter("fake", "fake")
    adapter.client.bearer = BearerToken(
        "fake", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    )
    response = Response()
    response.status_code = 200
    response._content = b'{"username":"fake","currentBalance":1.0}'
    adapter.client.session.request = Mock(return_value=response)
    adapter.account()
    headers = adapter.client.session.request.call_args.kwargs["headers"]
    assert headers["User-Agent"] == f"TextVerified-Python-TUI/{__version__}"
    adapter.close()


def test_malformed_sms_keeps_good_rows_and_discloses_partial_scan(capsys):
    from textverified.terminal.adapter import Adapter

    adapter = Adapter("fake", "fake")
    adapter.client._perform_action = Mock(
        return_value=_ActionResponse(
            dict(
                data=[{}, dict(id="good", to="001234", createdAt="2026-10-01T00:00:00Z", smsContent="safe")],
                hasNext=False,
            ),
            {},
        )
    )
    finite(adapter.messages(), adapter.account_scope, format="json", limit=None, sms=True, warnings=adapter.warnings)
    output = json.loads(capsys.readouterr().out)
    assert output["items"][0]["id"] == "good"
    assert output["meta"]["scan_complete"] is False
    assert output["meta"]["warnings"]
    adapter.close()


def test_bounded_100000_message_reconciliation():
    class LargeAccount:
        def messages(self, **kwargs):
            for i in range(100000):
                yield sms(str(i), body="x" * 256)

    feed = Feed(LargeAccount(), max_bodies=100)
    assert sum(1 for event in feed.reconcile()) == 100000
    assert len(feed.messages) == 100
    assert len(feed.digests) == 100000


def test_invalid_theme_falls_back_and_reset_is_available(service):
    from textverified.terminal.tui import TerminalApp

    config = service.config
    config.raw["appearance"] = {"theme": "custom:missing"}
    config.save()
    app = TerminalApp(service, config=Config())
    assert app.theme == "terminal" and app.style_error
    safe_app = TerminalApp(service, config=Config(), reset_style=True)
    assert safe_app.theme == "terminal" and not safe_app.style_error


def test_tui_slow_quote_is_discarded_when_form_changes(service):
    from textverified.terminal.tui import TerminalApp, Purchase, Confirm
    from textual.widgets import Input, Static

    async def scenario():
        started, release = threading.Event(), threading.Event()
        original = service.adapter.quote

        def slow(kind, request):
            started.set()
            release.wait(2)
            return original(kind, request)

        service.adapter.quote = slow
        app = TerminalApp(service, config=service.config)
        async with app.run_test(size=(100, 38)) as pilot:
            await pilot.pause()
            app.push_screen(Purchase("verification"))
            await pilot.pause()
            form = app.screen
            form.query_one("#service", Input).value = "example"
            await pilot.pause()
            form.quote()
            await pilot.pause()
            assert started.is_set()
            form.query_one("#service", Input).value = "changed"
            await pilot.pause()
            release.set()
            await app.workers.wait_for_complete()
            assert not isinstance(app.screen, Confirm)
            assert "discarded" in str(form.query_one("#quote-status", Static).render())
            assert service.adapter.submits == 0

    asyncio.run(scenario())


def test_watch_since_rebuilds_uncommitted_baseline_after_failure(service, monkeypatch):
    import requests

    calls = []

    def flaky(**kwargs):
        calls.append(True)
        yield sms("first", created="2026-10-01T00:00:00Z")
        if len(calls) == 1:
            raise requests.ConnectionError("fixture disconnect")
        yield sms("second", created="2026-10-01T01:00:00Z")

    service.adapter.messages = flaky
    monkeypatch.setattr(cli, "workflow", lambda ctx: service)
    elapsed = [0.0]
    monkeypatch.setattr(cli.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(cli.time, "sleep", lambda delay: elapsed.__setitem__(0, elapsed[0] + delay))
    result = CliRunner().invoke(
        cli.app, ["sms", "watch", "--since", "2026-10-01T00:00:00Z", "--timeout", "10", "--format", "ndjson"]
    )
    assert result.exit_code == 0, result.exception
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert [record["message"]["id"] for record in records] == ["first", "second"]
    assert all(record["replay"] for record in records)


def test_cached_login_round_trip_rotation_and_logout(service, monkeypatch):
    config = service.config
    config.save_credentials("email@example.com", "first-key")
    assert Config().credentials() == ("email@example.com", "first-key", "default")
    assert "first-key" not in config.path.read_text(encoding="utf-8")
    config.save_credentials("email@example.com", "rotated-key")
    assert Config().credentials() == ("email@example.com", "rotated-key", "default")
    assert "first-key" not in config.credentials_path.read_text(encoding="utf-8")
    if os.name != "nt":
        assert config.credentials_path.stat().st_mode & 0o777 == 0o600
        assert config.cache_directory.stat().st_mode & 0o777 == 0o700
    monkeypatch.setenv("TEXTVERIFIED_API_USERNAME", "environment@example.com")
    monkeypatch.setenv("TEXTVERIFIED_API_KEY", "environment-key")
    assert Config().credentials() == ("environment@example.com", "environment-key", None)
    assert Config().credentials("default") == ("email@example.com", "rotated-key", "default")
    monkeypatch.delenv("TEXTVERIFIED_API_USERNAME")
    monkeypatch.delenv("TEXTVERIFIED_API_KEY")
    config.remove_credentials()
    assert not config.credentials_path.exists()
    assert not Config().profiles
    with pytest.raises(TerminalError):
        Config().credentials()


def test_default_cache_location_and_xdg_override(tmp_path, monkeypatch):
    from pathlib import Path

    monkeypatch.delenv("TEXTVERIFIED_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert Config().credentials_path == tmp_path / ".cache" / "textverified" / "credentials.json"
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg-cache"))
    assert Config().credentials_path == tmp_path / "xdg-cache" / "textverified" / "credentials.json"


@pytest.mark.parametrize("accepted", [True, False])
def test_tui_login_only_email_and_key_saved_after_validation(service, monkeypatch, accepted):
    from textverified.terminal import tui
    from textual.widgets import Input

    adapter = FakeAdapter()
    adapter.account = Mock(return_value={"username": "email@example.com"})
    if not accepted:
        adapter.account.side_effect = ValueError("Invalid credentials")
    monkeypatch.setattr(tui, "Adapter", lambda *args: adapter)

    async def scenario():
        app = tui.TerminalApp(config=service.config)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.theme == "textverified-dark"
            assert len(app.screen.query(Input)) == 2
            assert app.focused.id == "login-user"
            app.screen.query_one("#login-user", Input).value = "email@example.com"
            app.screen.query_one("#login-key", Input).value = "test-key"
            await pilot.press("enter")
            assert app.focused.id == "login-key"
            await pilot.press("enter")
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert service.config.credentials_path.exists() == accepted
            assert isinstance(app.screen, tui.Login) != accepted
            if accepted:
                assert Config().credentials() == ("email@example.com", "test-key", "default")
        if app.application:
            app.application.close()

    asyncio.run(scenario())


def test_login_header_updates_before_initial_message_sync(service, monkeypatch):
    from textverified.terminal import tui
    from textual.widgets import Input, Static

    started, release = threading.Event(), threading.Event()
    adapter = FakeAdapter()
    adapter.username = "signed-in@example.com"
    adapter.account = Mock(return_value=dict(username=adapter.username, balance_amount="42.00"))
    original = adapter.messages

    def slow_messages(**kwargs):
        started.set()
        release.wait(5)
        yield from original(**kwargs)

    adapter.messages = slow_messages
    monkeypatch.setattr(tui, "Adapter", lambda *args: adapter)

    async def scenario():
        app = tui.TerminalApp(config=service.config)
        try:
            async with app.run_test(size=(80, 24)) as pilot:
                await pilot.pause()
                app.screen.query_one("#login-user", Input).value = adapter.username
                app.screen.query_one("#login-key", Input).value = "test-key"
                await pilot.press("enter", "enter")
                await pilot.pause()
                assert started.is_set()
                assert not isinstance(app.screen, tui.Login)
                header = str(app.query_one("#account-bar", Static).render())
                assert adapter.username in header
                assert "42.00" in header
                assert "Connected" in header
                assert "Authentication required" not in header
                assert adapter.account.call_count == 1
                release.set()
                await app.workers.wait_for_complete()
        finally:
            release.set()
            if app.application:
                app.application.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("height", [22, 32])
def test_inbox_body_and_readable_details(service, height):
    from textverified.terminal.tui import TerminalApp, Notice
    from textual.widgets import DataTable, TextArea

    body = "Your [service] code is 001234.\nKeep this message private."
    service.adapter.rows[0]["body"] = body

    async def scenario():
        app = TerminalApp(service, config=service.config)
        async with app.run_test(size=(100, height)) as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            app.action_inbox()
            table = app.query_one("#inbox-list", DataTable)
            assert [str(column.label) for column in table.ordered_columns] == ["Time", "To", "From", "Code", "Body"]
            row = table.get_row("external-inactive")
            assert "001234" in str(row[3])
            assert str(row[4]) == body.replace("\n", " ")
            await pilot.press("enter")
            await pilot.pause()
            area = (
                app.screen.query_one("#notice-text", TextArea)
                if isinstance(app.screen, Notice)
                else app.query_one("#details", TextArea)
            )
            assert body in area.text
            assert "Code: 001234" in area.text
            assert '"parsed_code"' not in area.text
            assert "observed_at" not in area.text
            if isinstance(app.screen, Notice):
                await pilot.press("escape")
            app.action_account()
            await pilot.pause()
            account = app.screen.query_one("#notice-text", TextArea).text
            assert "Email: fake" in account
            assert "Balance: 12.50" in account
            assert '"account"' not in account

    asyncio.run(scenario())


def test_successful_sms_sync_does_not_show_incomplete_during_resource_loading(service):
    from textverified.terminal.tui import TerminalApp
    from textual.widgets import Static

    started, release = threading.Event(), threading.Event()
    original = service.adapter.resources

    def slow_resources(*args, **kwargs):
        started.set()
        release.wait(5)
        yield from original(*args, **kwargs)

    service.adapter.resources = slow_resources

    async def scenario():
        app = TerminalApp(service, config=service.config)
        try:
            async with app.run_test(size=(100, 32)) as pilot:
                await pilot.pause()
                assert started.is_set()
                assert len(app.messages) == 2
                coverage = str(app.query_one("#coverage", Static).render())
                assert "2 retained messages" in coverage
                assert "incomplete" not in coverage.lower()
                release.set()
                await app.workers.wait_for_complete()
        finally:
            release.set()

    asyncio.run(scenario())
