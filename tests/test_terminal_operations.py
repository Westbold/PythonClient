"""Inbox, polling and rentals exercised through generated SDK fixtures."""
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

pytest.importorskip("rich")
from rich.console import Console
import textverified as tv
from textverified.terminal import cli
from .test_terminal import isolated, api
from .fixtures import mock_http_from_disk


def test_verification_preferences_are_quoted_and_transmitted(api):
    assert cli.main(["verify", "gmail", "--area-code", "415", "--area-code", "650", "--carrier", "att", "--yes"]) == 0
    quote = next(kw["json"] for _, url, kw in api if url.endswith("/pricing/verifications"))
    buy = next(kw["json"] for method, url, kw in api if method == "POST" and url.endswith("/api/pub/v2/verifications"))
    assert quote["areaCode"] is True and quote["carrier"] is True
    assert buy["areaCodeSelectOption"] == ["415", "650"]
    assert buy["carrierSelectOption"] == ["att"]
    assert buy["maxPrice"] == quote.get("price", 5.0)


@pytest.mark.parametrize("mock", [False, True])
@pytest.mark.parametrize("action", ["list", "show", "resume", "cancel"])
def test_existing_verifications_use_sdk_without_buying(api, mock_http_from_disk, monkeypatch, capsys, action, mock):
    def cancellable(response, method, url, **kwargs):
        if isinstance(response, dict) and "cancel" in response:
            response["cancel"]["canCancel"] = True
        return response

    mock_http_from_disk.add_hook(cancellable)
    args = (["--mock"] if mock else []) + ["verifications", action]
    if action != "list" and not mock:
        args.append("string")
    if action == "cancel":
        args.append("--yes")
    assert cli.main(args) == 0
    assert not any(method == "POST" and url.endswith("/api/pub/v2/verifications") for method, url, _ in api)
    if action == "resume":
        assert capsys.readouterr().out.rstrip().endswith("001234")
    if action == "cancel":
        assert any(method == "POST" and url.endswith("/cancel") for method, url, _ in api)


def test_verification_cancel_checks_eligibility(api, mock_http_from_disk, capsys):
    def disallow(response, method, url, **kwargs):
        if isinstance(response, dict) and "cancel" in response:
            response["cancel"]["canCancel"] = False
        return response

    mock_http_from_disk.add_hook(disallow)
    assert cli.main(["verifications", "cancel", "string", "--yes"]) == 1
    assert "does not currently allow" in capsys.readouterr().err
    assert not any(method == "POST" and url.endswith("/cancel") for method, url, _ in api)


def test_sms_api_error_keeps_stdout_empty(api, monkeypatch, capsys):
    client = cli._client()
    monkeypatch.setattr(
        tv.sms_api.SMSApi, "list", Mock(side_effect=tv.TextVerifiedError("Unauthorized", "Invalid key"))
    )
    monkeypatch.setattr(cli, "_client", lambda **kw: client)
    assert cli.main(["inbox"]) == 1
    output = capsys.readouterr()
    assert output.out == "" and output.err == "Invalid key\n"


def test_existing_verification_cancel_requires_confirmation(api, mock_http_from_disk, capsys):
    def allow(response, method, url, **kwargs):
        if isinstance(response, dict) and "cancel" in response:
            response["cancel"]["canCancel"] = True
        return response

    mock_http_from_disk.add_hook(allow)
    assert cli.main(["verifications", "cancel", "string"]) == 2
    assert "pass --yes" in capsys.readouterr().err
    assert not any(method == "POST" and url.endswith("/cancel") for method, url, _ in api)


def test_existing_live_verification_requires_id_before_network(api, capsys):
    assert cli.main(["verifications", "resume"]) == 1
    assert "ID is required" in capsys.readouterr().err
    assert api == []


def test_accepted_verification_purchase_reports_recovery_without_retry(api, mock_http_from_disk, capsys):
    def fail_details(response, method, url, **kwargs):
        if method == "GET" and url.endswith("/verifications/string"):
            raise cli.requests.ConnectionError("Details unavailable")
        return response

    mock_http_from_disk.add_hook(fail_details)
    assert cli.main(["verify", "gmail", "--yes"]) == 1
    error = capsys.readouterr().err
    assert "Purchase accepted" in error and "tv verifications show string" in error
    assert sum(method == "POST" and url.endswith("/api/pub/v2/verifications") for method, url, _ in api) == 1


def test_purchase_transport_failure_reports_unknown_outcome(api, mock_http_from_disk, capsys):
    def disconnect(response, method, url, **kwargs):
        if method == "POST" and url.endswith("/api/pub/v2/verifications"):
            raise cli.requests.ConnectionError("Connection lost")
        return response

    mock_http_from_disk.add_hook(disconnect)
    assert cli.main(["verify", "gmail", "--yes"]) == 1
    assert "outcome is unknown" in capsys.readouterr().err


def test_rental_number_type_matches_catalog_quote_and_purchase(rental_api):
    assert cli.main(["rentals", "buy", "gmail", "--number-type", "voip", "--yes"]) == 0
    catalog = next(kw["params"] for _, url, kw in rental_api if url.endswith("/services"))
    assert catalog["numberType"] == "voip"
    for ending in ("/pricing/rentals", "/reservations/rental"):
        payload = next(kw["json"] for method, url, kw in rental_api if method == "POST" and url.endswith(ending))
        assert payload["numberType"] == "voip"


@pytest.mark.parametrize("stage", ["sale", "rental"])
def test_rental_purchase_details_failure_preserves_sale(rental_api, mock_http_from_disk, capsys, stage):
    def fail(response, method, url, **kwargs):
        target = "/sales/" if stage == "sale" else "/reservations/rental/renewable/"
        if method == "GET" and target in url:
            raise cli.requests.ConnectionError("Details unavailable")
        return response

    mock_http_from_disk.add_hook(fail)
    assert cli.main(["rentals", "buy", "gmail", "--yes"]) == 1
    error = capsys.readouterr().err
    assert "tv rentals sale" in error and "repeat the purchase" in error
    assert sum(method == "POST" and url.endswith("/reservations/rental") for method, url, _ in rental_api) == 1


def test_sale_can_be_recovered_without_purchase(rental_api, capsys):
    assert cli.main(["rentals", "sale", "sale1"]) == 0
    assert "Sale" in capsys.readouterr().out
    assert not any(method == "POST" and url.endswith("/reservations/rental") for method, url, _ in rental_api)


@pytest.mark.parametrize(
    "args",
    [
        ["services", "gmail"],
        ["rentals"],
        ["rentals", "services", "gmail"],
        ["rentals", "show", "r1"],
        ["verifications", "show", "string"],
    ],
)
def test_resource_lists_are_tsv_in_pipes(rental_api, capsys, args):
    import csv
    import io

    assert cli.main(args) == 0
    output = capsys.readouterr().out
    rows = list(csv.reader(io.StringIO(output), delimiter="\t"))
    assert len(rows) >= 2
    assert len(rows[0]) >= 3
    assert all(len(row) == len(rows[0]) for row in rows)
    assert "\x1b" not in output


@pytest.mark.parametrize("command,limit", [("rentals", 5), ("verifications", 5), ("rentals", 8), ("verifications", 8)])
def test_recent_lists_bound_pagination_and_sort_creation_times(api, mock_http_from_disk, capsys, command, limit):
    from copy import deepcopy
    import csv
    import io

    def page(response, method, url, **kwargs):
        if not isinstance(response, dict) or "data" not in response or "/sms" in url:
            return response
        if not ("/rental/" in url or url.split("?", 1)[0].endswith("/verifications")):
            return response
        template = response["data"][0]
        second = "page=2" in url
        kind = "renewable" if url.split("?", 1)[0].endswith("/renewable") else "other"
        indices = [6, 5, 8, 7, 9] if second else [1, 0, 3, 2, 4]
        response["data"] = []
        for index in indices:
            item = deepcopy(template)
            item["id"] = f"{kind}-{index}"
            item["createdAt"] = (
                datetime(2026, 10, 5, 12 if kind == "renewable" else 10, tzinfo=timezone.utc) - timedelta(days=index)
            ).isoformat()
            response["data"].append(item)
        response["hasNext"] = True
        response["links"] = {"next": {"method": "GET", "href": url.split("?", 1)[0] + "?page=2"}}
        return response

    mock_http_from_disk.add_hook(page)
    args = [command] if limit == 5 else [command, "list", "--limit", str(limit)]
    assert cli.main(args) == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert rows[0][-1] == "Created"
    assert len(rows) == limit + 1
    times = [datetime.fromisoformat(row[-1]) for row in rows[1:]]
    assert times == sorted(times, reverse=True)
    fetches = [
        url
        for method, url, _ in api
        if method == "GET" and ("/rental/" in url or url.split("?", 1)[0].endswith("/verifications"))
    ]
    assert len(fetches) == (2 if command == "rentals" else 1) * (2 if limit == 8 else 1)


def test_timestamp_uses_local_timezone_and_keeps_offset_in_pipes(monkeypatch):
    stamp = datetime(2026, 10, 6, 1, 2, 3, tzinfo=timezone.utc)
    monkeypatch.setattr(cli, "interactive_output", lambda: False)
    assert cli.local_timestamp(stamp) == stamp.astimezone().isoformat(sep=" ", timespec="seconds")
    assert cli.local_timestamp(stamp.replace(tzinfo=None)) == cli.local_timestamp(stamp)
    monkeypatch.setattr(cli, "interactive_output", lambda: True)
    assert cli.local_timestamp(stamp) == stamp.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def test_rental_feeds_are_fetched_concurrently(api, monkeypatch):
    import threading
    from textverified.reservations_api import ReservationsAPI

    barrier = threading.Barrier(2, timeout=2)
    calls = []

    def rentals(self):
        calls.append(threading.get_ident())
        barrier.wait()
        return iter([])

    monkeypatch.setattr(ReservationsAPI, "list_renewable", rentals)
    monkeypatch.setattr(ReservationsAPI, "list_nonrenewable", rentals)
    assert cli.main(["rentals", "list"]) == 0
    assert len(set(calls)) == 2


@pytest.mark.parametrize("limit", [5, 8])
def test_inbox_default_and_override_are_recent_bounded_and_timestamp_last(api, mock_http_from_disk, capsys, limit):
    from copy import deepcopy
    import csv
    import io

    def page(response, method, url, **kwargs):
        if not url.split("?", 1)[0].endswith("/sms"):
            return response
        template = response["data"][0]
        response["data"] = []
        for index in [6, 5, 8, 7, 9] if "page=2" in url else [1, 0, 3, 2, 4]:
            item = deepcopy(template)
            item["id"] = f"s{index}"
            item["createdAt"] = (datetime(2026, 10, 6, tzinfo=timezone.utc) - timedelta(days=index)).isoformat()
            response["data"].append(item)
        response["hasNext"] = True
        response["links"] = {"next": {"method": "GET", "href": url.split("?", 1)[0] + "?page=2"}}
        return response

    mock_http_from_disk.add_hook(page)
    assert cli.main(["inbox"] + (["--limit", str(limit)] if limit != 5 else [])) == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert rows[0] == ["ID", "To", "From", "Code", "Body", "Received"]
    assert len(rows) == limit + 1
    stamps = [datetime.fromisoformat(row[-1]) for row in rows[1:]]
    assert stamps == sorted(stamps, reverse=True)
    assert sum("/sms" in url for _, url, _ in api) == (1 if limit == 5 else 2)


@pytest.mark.parametrize("command", [["services"], ["rentals", "services"]])
@pytest.mark.parametrize("limit", [5, 8])
def test_catalog_limits_filter_before_truncating_and_quote_only_displayed(
    api, mock_http_from_disk, capsys, command, limit
):
    from copy import deepcopy
    import csv
    import io

    def many(response, method, url, **kwargs):
        if url.endswith("/services"):
            template = response[0]
            response = [dict(deepcopy(template), serviceName=f"target{index:02}") for index in range(20)]
        return response

    mock_http_from_disk.add_hook(many)
    assert cli.main(command + ["target", *(["--limit", str(limit)] if limit != 5 else [])]) == 0
    output = capsys.readouterr()
    rows = list(csv.reader(io.StringIO(output.out), delimiter="\t"))
    assert len(rows) == limit + 1
    assert "--limit" in output.err and "20" in output.err
    quotes = [url for _, url, _ in api if url.endswith("/pricing/verifications")]
    assert len(quotes) == (limit if command == ["services"] else 0)


def test_inbox_terminal_hides_id_and_previews_body_with_local_time_last(api, mock_http_from_disk, monkeypatch):
    import io
    from rich.console import Console

    def body(response, method, url, **kwargs):
        if url.endswith("/sms"):
            response["data"][0]["smsContent"] = "first line\nsecond line " + "long body " * 30
        return response

    mock_http_from_disk.add_hook(body)
    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, width=160, color_system=None))
    monkeypatch.setattr(cli, "interactive_output", lambda: True)
    monkeypatch.setattr(cli, "spinner", lambda label: cli.nullcontext())
    assert cli.main(["inbox"]) == 0
    text = output.getvalue()
    header = next(line for line in text.splitlines() if "Received" in line)
    assert header.index("Received") > header.index("Body")
    assert " ID " not in header
    assert "first line second line" in text
    assert text.count("long body") < 5


def test_poll_does_not_drop_messages_above_snapshot_limit(api, monkeypatch, capsys):
    import csv
    import io

    now = datetime.now(timezone.utc)
    batch = [
        tv.Sms(
            id=f"s{i}",
            to_value="14155550123",
            from_value="12345",
            created_at=now,
            encrypted=False,
            sms_content=f"body {i}",
        )
        for i in range(8)
    ]
    monkeypatch.setattr(tv.sms_api.SMSApi, "incoming", Mock(return_value=batch))
    assert cli.main(["poll", "--since", (now - timedelta(seconds=10)).isoformat()]) == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert len(rows) == 9
    assert [row[0] for row in rows[1:]] == [f"s{i}" for i in range(8)]


@pytest.mark.parametrize(
    "command", [["inbox"], ["verifications", "list"], ["rentals", "list"], ["services"], ["rentals", "services"]]
)
def test_every_limited_command_supports_offset(api, mock_http_from_disk, capsys, command):
    from copy import deepcopy
    import csv
    import io

    def records(response, method, url, **kwargs):
        if url.endswith("/services"):
            return [dict(deepcopy(response[0]), serviceName=f"service{i:02}") for i in range(10)]
        if not isinstance(response, dict) or "data" not in response or not response["data"]:
            return response
        if not ("/sms" in url or "/rental/" in url or url.split("?", 1)[0].endswith("/verifications")):
            return response
        template = response["data"][0]
        start = 5 if "page=2" in url else 0
        response["data"] = []
        for index in range(start, start + 5):
            item = deepcopy(template)
            item["id"] = f"row{index}"
            item["createdAt"] = (datetime(2026, 10, 6, tzinfo=timezone.utc) - timedelta(days=index)).isoformat()
            response["data"].append(item)
        response["hasNext"] = start == 0
        response["links"] = {"next": {"method": "GET", "href": url.split("?", 1)[0] + "?page=2"}} if start == 0 else {}
        return response

    mock_http_from_disk.add_hook(records)
    flags = ["--kind", "renewable"] if command == ["rentals", "list"] else []
    assert cli.main([*command, *flags, "--offset", "3", "--limit", "4"]) == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert len(rows) == 5
    assert [row[0] for row in rows[1:]] == [
        f"service{i:02}" if command[-1] == "services" else f"row{i}" for i in range(3, 7)
    ]


@pytest.mark.parametrize(
    "command", [["inbox"], ["verifications", "list"], ["rentals", "list"], ["services"], ["rentals", "services"]]
)
def test_negative_offset_is_rejected_before_network(api, command):
    with pytest.raises(SystemExit) as error:
        cli.main([*command, "--offset", "-1"])
    assert error.value.code == 2
    assert api == []


@pytest.mark.parametrize(
    "command", [["inbox"], ["verifications", "list"], ["rentals", "list"], ["services"], ["rentals", "services"]]
)
def test_offset_past_end_emits_no_data(api, capsys, command):
    assert cli.main([*command, "--offset", "10000"]) == 0
    assert capsys.readouterr().out == ""


def test_rental_offset_applies_once_after_merging_types(api, mock_http_from_disk, capsys):
    from copy import deepcopy
    import csv
    import io

    def rows(response, method, url, **kwargs):
        if not (url.endswith("/rental/renewable") or url.endswith("/rental/nonrenewable")):
            return response
        renewable = url.endswith("/renewable")
        template = response["data"][0]
        response["data"] = []
        for i in range(5):
            item = deepcopy(template)
            item["id"] = f"{'r' if renewable else 'n'}{i}"
            item["createdAt"] = (
                datetime(2026, 10, 6, 12 if renewable else 10, tzinfo=timezone.utc) - timedelta(days=i)
            ).isoformat()
            response["data"].append(item)
        response["hasNext"] = False
        return response

    mock_http_from_disk.add_hook(rows)
    assert cli.main(["rentals", "list", "--offset", "3", "--limit", "2"]) == 0
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert [row[0] for row in rows[1:]] == ["n1", "r2"]


@pytest.mark.parametrize("command", ["rentals", "verifications"])
def test_interactive_list_is_compact_and_timestamp_is_last(api, monkeypatch, capsys, command):
    import io
    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, width=100, color_system=None))
    monkeypatch.setattr(cli, "interactive_output", lambda: True)
    monkeypatch.setattr(cli, "spinner", lambda label: cli.nullcontext())
    assert cli.main([command]) == 0
    text = output.getvalue()
    header = next(line for line in text.splitlines() if "Created" in line)
    assert header.index("Created") > header.index("State")
    assert " ID " not in header and "Always on" not in header
    assert "verificationPending" not in text


@pytest.fixture(autouse=True)
def wide_console(monkeypatch):
    monkeypatch.setattr(cli, "console", Console(width=200, color_system=None))


@pytest.mark.parametrize(
    "flags,params",
    [
        ([], {}),
        (["--number", "14155550123"], {"to": "14155550123"}),
        (
            ["--line-number", "14155550123", "--type", "renewable"],
            {"to": "14155550123", "reservationType": "renewable"},
        ),
        (
            ["--reservation-id", "v1", "--type", "verification"],
            {"reservationId": "v1", "reservationType": "verification"},
        ),
        (["--line-id", "r1"], {"reservationId": "r1"}),
        (["--type", "nonrenewable"], {"reservationType": "nonrenewable"}),
    ],
)
def test_inbox_filters_and_body(api, flags, params, capsys):
    assert cli.main(["inbox", *flags]) == 0
    assert [kwargs["params"] for _, url, kwargs in api if url.endswith("/sms")] == [params]
    output = capsys.readouterr().out
    assert "Body" in output and "To" in output and "Code" in output
    assert "001234" in output


def test_inbox_follows_sdk_pagination(api, mock_http_from_disk, capsys):
    def page(response, method, url, **kwargs):
        if "/sms" not in url:
            return response
        second = "page=2" in url
        response["data"] = [response["data"][0]]
        response["data"][0]["id"] = "page-two" if second else "page-one"
        response["data"][0]["smsContent"] = "page two body" if second else "page one body"
        response["hasNext"] = not second
        response["links"] = (
            {} if second else {"next": {"method": "GET", "href": "https://www.textverified.com/api/pub/v2/sms?page=2"}}
        )
        return response

    mock_http_from_disk.add_hook(page)
    assert cli.main(["inbox", "--limit", "2"]) == 0
    output = capsys.readouterr().out
    assert "page one body" in output and "page two body" in output
    assert sum("/sms" in url for _, url, _ in api) == 2


def test_poll_uses_sdk_incoming_with_exact_id(api, mock_http_from_disk, monkeypatch, capsys):
    def fresh(response, method, url, **kwargs):
        if url.endswith("/sms"):
            for message in response["data"]:
                message["createdAt"] = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
                message["smsContent"] = "new SMS body"
        return response

    mock_http_from_disk.add_hook(fresh)
    monkeypatch.setattr("textverified.sms_api.time.sleep", lambda seconds: None)
    assert cli.main(["poll", "--line-id", "r1", "--type", "renewable", "--timeout", "1"]) == 0
    assert "new SMS body" in capsys.readouterr().out
    assert [kwargs["params"] for _, url, kwargs in api if url.endswith("/sms")] == [
        {"reservationId": "r1", "reservationType": "renewable"}
    ]


def test_poll_follow_deduplicates_without_stopping_early(api, monkeypatch, capsys):
    client = cli._client()
    now = datetime.now(timezone.utc)

    def message(id, body):
        return tv.Sms(
            id=id, to_value="14155550123", from_value="12345", created_at=now, encrypted=False, sms_content=body
        )

    first, second = message("s1", "first body"), message("s2", "second body")
    incoming = Mock(side_effect=[[first], [first], [first, second], []])
    monkeypatch.setattr(tv.sms_api.SMSApi, "incoming", incoming)
    monkeypatch.setattr(cli, "_client", lambda **kwargs: client)
    assert cli.main(["poll", "--follow", "--since", (now - timedelta(seconds=10)).isoformat()]) == 0
    output = capsys.readouterr().out
    assert output.count("first body") == 1
    assert output.count("second body") == 1
    assert incoming.call_count == 4


def test_poll_timeout_does_not_emit_old_sms(api, capsys):
    assert cli.main(["poll", "--timeout", "0"]) == 1
    assert "No new SMS" in capsys.readouterr().err
    assert not any(url.endswith("/sms") for _, url, _ in api)


@pytest.mark.parametrize(
    "flags",
    [
        ["--limit", "0"],
        ["--number", "123", "--line-id", "r1"],
    ],
)
def test_invalid_inbox_arguments_fail_before_requests(api, flags):
    with pytest.raises(SystemExit):
        cli.main(["inbox", *flags])
    assert api == []


@pytest.mark.parametrize("flags", [["--interval", "0"], ["--timeout", "-2"], ["--timeout", "nan"]])
def test_invalid_poll_arguments_fail_before_requests(api, flags):
    with pytest.raises(SystemExit):
        cli.main(["poll", *flags])
    assert api == []


@pytest.fixture
def rental_api(api, mock_http_from_disk):
    def links(response, method, url, **kwargs):
        if (
            method.upper() == "GET"
            and "/rental/" in url
            and "/mock_" in url
            and isinstance(response, dict)
            and "id" in response
        ):
            response["id"] = url.rsplit("/", 1)[-1]
        if method.upper() == "POST" and url.endswith("/reservations/rental"):
            return {"method": "GET", "href": "https://www.textverified.com/api/pub/v2/sales/sale1"}
        if "/sales/" in url:
            response["reservations"] = response["reservations"][:1]
        if "/reservations/" in url and "/" not in url.split("/reservations/", 1)[1]:
            kind = "nonrenewable" if "non1" in url or "mock_nonren" in url else "renewable"
            resource = url.rsplit("/", 1)[-1] if "mock_" in url else "string"
            return {
                "method": "GET",
                "href": f"https://www.textverified.com/api/pub/v2/reservations/rental/{kind}/{resource}",
            }
        if method.upper() == "POST" and url.endswith("/wake-requests"):
            return {"method": "GET", "href": "https://www.textverified.com/api/pub/v2/wake-requests/w1"}
        return response

    mock_http_from_disk.add_hook(links)
    return api


def test_rentals_list_unifies_both_types(api, capsys):
    assert cli.main(["rentals"]) == 0
    output = capsys.readouterr().out
    assert "renewable" in output and "nonrenewable" in output
    assert any(url.endswith("/rental/renewable") for _, url, _ in api)
    assert any(url.endswith("/rental/nonrenewable") for _, url, _ in api)


@pytest.mark.parametrize("kind", ["renewable", "nonrenewable"])
def test_rental_catalog_uses_correct_api_type(api, kind):
    assert cli.main(["rentals", "services", "gmail", "--kind", kind]) == 0
    catalog = [kwargs for _, url, kwargs in api if url.endswith("/services")]
    assert catalog[0]["params"]["reservationType"] == kind
    assert not any("/pricing/verifications" in url for _, url, _ in api)


@pytest.mark.parametrize("mock", [False, True])
def test_rental_purchase_quotes_and_follows_sale_links(rental_api, capsys, mock):
    args = (["--mock"] if mock else []) + [
        "rentals",
        "buy",
        "gmail",
        "--kind",
        "nonrenewable",
        "--duration",
        "sevenDay",
        "--always-on",
        "--area-code",
        "415",
        "--yes",
    ]
    assert cli.main(args) == 0
    prices = [kwargs["json"] for _, url, kwargs in rental_api if url.endswith("/pricing/rentals")]
    buys = [
        kwargs["json"]
        for method, url, kwargs in rental_api
        if method == "POST" and url.endswith("/reservations/rental")
    ]
    assert len(prices) == len(buys) == 1
    assert prices[0]["serviceName"] == buys[0]["serviceName"] == ("test_success" if mock else "gmail")
    assert prices[0]["duration"] == buys[0]["duration"] == "sevenDay"
    assert prices[0]["isRenewable"] is buys[0]["isRenewable"] is False
    assert buys[0]["alwaysOn"] is True
    assert buys[0]["allowBackOrderReservations"] is False
    assert buys[0]["areaCodeSelectOption"] == ["415"]
    assert "Sale" in capsys.readouterr().out


def test_rental_purchase_requires_confirmation(rental_api):
    assert cli.main(["rentals", "buy", "gmail"]) == 2
    assert not any(method == "POST" and url.endswith("/reservations/rental") for method, url, _ in rental_api)


@pytest.mark.parametrize("id", ["r1", "non1"])
def test_rental_show_follows_sdk_type_link(rental_api, id, capsys):
    assert cli.main(["rentals", "show", id]) == 0
    assert "Created" in capsys.readouterr().out


@pytest.mark.parametrize(
    "args,path,key,value",
    [
        (["renew", "r1", "--yes"], "/renewable/string/renew", None, None),
        (["extend", "non1", "--duration", "sevenDay", "--yes"], "/rentals/extensions", "extensionDuration", "sevenDay"),
        (["refund", "non1", "--yes"], "/nonrenewable/string/refund", None, None),
        (
            ["update", "r1", "--no-renewal", "--notes", "my line", "--tags", "work"],
            "/renewable/string",
            "includeForRenewal",
            False,
        ),
    ],
)
def test_rental_management_uses_sdk_requests(rental_api, args, path, key, value):
    assert cli.main(["rentals", *args]) == 0
    requests = [kwargs for method, url, kwargs in rental_api if method == "POST" and url.endswith(path)]
    assert len(requests) == 1
    if key:
        assert requests[0]["json"][key] == value


def test_wake_follows_sdk_wake_link(rental_api, capsys):
    assert cli.main(["rentals", "wake", "r1"]) == 0
    assert "Wake request" in capsys.readouterr().out
    assert [
        kwargs["json"] for method, url, kwargs in rental_api if method == "POST" and url.endswith("/wake-requests")
    ] == [{"reservationId": "r1"}]


def test_mock_does_not_mutate_real_rental(rental_api, capsys):
    assert cli.main(["--mock", "rentals", "renew", "r1", "--yes"]) == 0
    requests = [(method, url) for method, url, _ in rental_api if "/reservations/" in url]
    assert all("r1" not in url for _, url in requests)
    assert any(method == "POST" and "/mock_ren_expired_30d/renew" in url for method, url in requests)


@pytest.mark.parametrize("action", ["health", "notes", "backorder"])
def test_rental_read_commands_use_sdk_records(rental_api, action):
    assert cli.main(["rentals", action, "r1"]) == 0


def test_reactivation_uses_api_quote_as_price_cap(rental_api):
    assert cli.main(["rentals", "reactivate", "r1", "--yes"]) == 0
    requests = [(method, kwargs) for method, url, kwargs in rental_api if url.endswith("/reactivate")]
    assert [method for method, _ in requests] == ["GET", "POST"]
    assert requests[1][1]["json"]["maxPrice"] == 12.5


def test_nonrenewable_cannot_use_overdue_renewal(rental_api, capsys):
    assert cli.main(["rentals", "renew", "non1", "--yes"]) == 1
    assert "rentals extend" in capsys.readouterr().err
    assert not any(method == "POST" for method, url, _ in rental_api if "/reservations/" in url)


def test_inbox_since_excludes_old_messages(api, capsys):
    assert cli.main(["inbox", "--since", datetime.now(timezone.utc).isoformat()]) == 0
    assert "No SMS matches" in capsys.readouterr().err


@pytest.mark.parametrize("color,ansi", [("auto", False), ("always", False), ("never", False)])
def test_piped_inbox_uses_tsv_without_redraws(api, monkeypatch, color, ansi):
    import csv
    import io
    import re

    output = io.StringIO()
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=True, width=30))
    monkeypatch.setattr(cli, "Live", lambda *a, **kw: pytest.fail("Pipes must not start animation"))
    if color == "auto":
        monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=False, width=30))
    assert cli.main(["--color=" + color, "inbox"]) == 0
    raw = output.getvalue()
    assert ("\x1b[" in raw) is ansi
    plain = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    assert "\x1b" not in plain
    assert "┏" not in plain
    rows = list(csv.reader(io.StringIO(plain), delimiter="\t"))
    assert rows[0] == ["ID", "To", "From", "Code", "Body", "Received"]
    assert all(len(row) == 6 for row in rows)
    assert rows[1][3] == "001234"


def test_piped_inbox_preserves_long_multiline_bodies(api, mock_http_from_disk, monkeypatch):
    import csv
    import io

    body = "a" * 200 + "\tsecond field\nnext line"

    def content(response, method, url, **kwargs):
        if url.endswith("/sms"):
            for message in response["data"]:
                message["smsContent"] = body
        return response

    mock_http_from_disk.add_hook(content)
    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, width=20))
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    assert cli.main(["inbox"]) == 0
    rows = list(csv.reader(io.StringIO(output.getvalue()), delimiter="\t"))
    assert rows[1][4] == body


def test_terminal_inbox_keeps_table_with_no_animation(api, monkeypatch):
    import io

    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=True, color_system=None, width=160))
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli, "Live", lambda *a, **kw: pytest.fail("--no-animation disables spinners"))
    assert cli.main(["--no-animation", "inbox"]) == 0
    assert any(character in output.getvalue() for character in ("\u250f", "\u250c"))
    assert "\t" not in output.getvalue()


def test_forcing_color_in_piped_verification_does_not_start_live_display(api, monkeypatch, capsys):
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(cli, "Live", lambda *a, **kw: pytest.fail("Color must not force animation"))
    assert cli.main(["--color=always", "--mock", "verify", "gmail", "--yes"]) == 0
    assert capsys.readouterr().out.rstrip().splitlines()[-1] == "001234"


def test_forcing_color_in_piped_poll_does_not_start_animation(api, monkeypatch):
    import io
    from textverified.terminal import messages

    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, width=30))
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    monkeypatch.setattr(cli, "Live", lambda *a, **kw: pytest.fail("Piped polling must not animate"))
    client = cli._client()
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    sms = tv.Sms(id="s1", to_value="14155550123", created_at=now, encrypted=False, sms_content="hello")
    monkeypatch.setattr(tv.sms_api.SMSApi, "incoming", lambda *a, **kw: iter([sms]))
    monkeypatch.setattr(cli, "_client", lambda **kw: client)
    assert cli.main(["--color=always", "poll"]) == 0
    assert "hello" in output.getvalue()
    assert "\x1b" not in output.getvalue()
    assert "Waiting for SMS" not in output.getvalue()
    assert "[ .... ]" not in output.getvalue()
    assert output.getvalue().startswith("ID\tTo\t")


@pytest.mark.parametrize(
    "flags,resource",
    [
        ([], "mock_ver_success"),
        (["--type", "renewable"], "mock_ren_30d"),
        (["--type", "nonrenewable", "--line-id", "real-id"], "mock_nonren_30d"),
        (["--number", "14155550123"], "mock_ver_success"),
        (["--reservation-id", "mock_ver_pending"], "mock_ver_pending"),
    ],
)
def test_mock_poll_selects_server_resource_and_accepts_fixed_timestamps(api, flags, resource, capsys):
    assert cli.main(["--mock", "poll", *flags, "--interval", "0.001", "--timeout", "1"]) == 0
    output = capsys.readouterr().out
    assert "001234" in output
    requests = [kwargs for _, url, kwargs in api if url.endswith("/sms")]
    assert requests[0]["params"]["reservationId"] == resource
    assert "to" not in requests[0]["params"]


def test_mock_inbox_combines_all_reservation_types(api):
    assert cli.main(["--mock", "inbox"]) == 0
    scopes = [kwargs["params"] for _, url, kwargs in api if url.endswith("/sms")]
    assert {(scope["reservationId"], scope["reservationType"]) for scope in scopes} == {
        ("mock_ver_success", "verification"),
        ("mock_ren_30d", "renewable"),
        ("mock_nonren_30d", "nonrenewable"),
    }


@pytest.mark.parametrize(
    "action", ["show", "backorder", "health", "notes", "wake", "update", "renew", "extend", "refund", "reactivate"]
)
def test_mock_routes_rental_commands_through_sdk_without_real_ids(rental_api, action):
    options = {
        "update": ["--notes", "mock note"],
        "extend": ["--duration", "sevenDay", "--yes"],
        "renew": ["--yes"],
        "refund": ["--yes"],
        "reactivate": ["--yes"],
    }.get(action, [])
    assert cli.main(["--mock", "rentals", action, *options]) == 0
    # Every resource operation starts from a documented server mock ID.
    resource_requests = [
        (method, url, kwargs)
        for method, url, kwargs in rental_api
        if "/api/pub/v2/reservations/" in url or "/backorders/" in url
    ]
    assert all("mock_" in url or url.endswith("/extensions") for _, url, _ in resource_requests)
    if action == "extend":
        assert [
            kwargs["json"]["rentalId"] for method, url, kwargs in resource_requests if url.endswith("/extensions")
        ] == ["mock_nonren_30d"]


def test_mock_rental_list_reads_mock_details_instead_of_live_lists(rental_api):
    assert cli.main(["--mock", "rentals"]) == 0
    urls = [url for _, url, _ in rental_api]
    assert any(url.endswith("/renewable/mock_ren_30d") for url in urls)
    assert any(url.endswith("/nonrenewable/mock_nonren_30d") for url in urls)
    assert not any(url.endswith("/rental/renewable") or url.endswith("/rental/nonrenewable") for url in urls)


def test_live_rental_actions_still_require_an_id(rental_api, capsys):
    assert cli.main(["rentals", "wake"]) == 1
    assert "required without --mock" in capsys.readouterr().err
    assert rental_api == []


@pytest.mark.parametrize("animate", [True, False])
def test_terminal_poll_has_only_one_wait_indicator(api, monkeypatch, animate):
    import io
    from contextlib import contextmanager

    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=True, color_system=None, width=160))
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    now = datetime.now(timezone.utc) + timedelta(seconds=1)
    sms = tv.Sms(id="s1", to_value="14155550123", created_at=now, encrypted=False, sms_content="hello")
    monkeypatch.setattr(tv.sms_api.SMSApi, "incoming", lambda *a, **kw: iter([sms]))
    waits = []

    @contextmanager
    def spinner(label):
        if cli.ANIMATE:
            waits.append(label)
        yield

    monkeypatch.setattr(cli, "spinner", spinner)
    args = ([] if animate else ["--no-animation"]) + ["poll"]
    assert cli.main(args) == 0
    assert len(waits) == int(animate)
    assert ("Waiting for SMS" in output.getvalue()) is (not animate)
    assert "[ .... ]" not in output.getvalue()


def test_piped_poll_timeout_keeps_stdout_empty(api, capsys):
    assert cli.main(["--color=always", "poll", "--timeout", "0"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "No new SMS before the timeout.\n"
