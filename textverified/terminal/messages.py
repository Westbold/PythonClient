"""SMS inbox and polling through the SDK."""
from datetime import datetime, timezone
from itertools import islice, chain
import time

from rich.table import Table
from rich.text import Text
from textverified import Reservation, ReservationType, TestMode
from . import cli as ui


def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Use an ISO 8601 timestamp for --since.") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _filters(client, args):
    kind = ReservationType(args.type) if args.type else None
    data = None
    reservation_id = args.reservation_id
    number = args.number
    if client.test_mode == TestMode.MOCK_SUCCESS:
        if not reservation_id or not reservation_id.startswith("mock_"):
            reservation_id = ui.mock_reservation_id(kind or ReservationType.VERIFICATION)
        number = None
    if reservation_id:
        # SMS.list reads the ID from this object; its type filter is a separate argument.
        data = Reservation(id=reservation_id, reservation_type=kind or ReservationType.VERIFICATION, service_name="")
    return dict(data=data, to_number=number, reservation_type=kind)


def _unique(messages):
    seen = set()
    for message in messages:
        if message.id not in seen:
            seen.add(message.id)
            yield message


def _display(messages):
    headings = ("ID", "To", "From", "Code", "Body", "Received")
    rows = [
        (
            message.id,
            message.to_value,
            message.from_value or "",
            message.parsed_code or "",
            message.sms_content or ("[encrypted]" if message.encrypted else ""),
            ui.local_timestamp(message.created_at),
        )
        for message in messages
    ]
    if not ui.interactive_output():
        ui.write_records(headings, rows)
        return
    table = Table(header_style=ui.brand.CYAN, border_style=ui.brand.BRAND)
    for name in headings[1:]:
        table.add_column(name, overflow="ellipsis", no_wrap=True, max_width=32 if name == "Body" else None)
    for row in rows:
        table.add_row(*[Text(" ".join(str(value).split())) for value in row[1:]])
    ui.console.print(table)


def _notice(message):
    if ui.interactive_output():
        ui.status("info", message)
    else:
        print(message, file=ui.sys.stderr)


def run(client, args):
    if args.command == "inbox":
        since = _timestamp(args.since) if args.since else None
        with ui.spinner("loading SMS"):
            scopes = [_filters(client, args)]
            if client.test_mode == TestMode.MOCK_SUCCESS and not (args.type or args.reservation_id or args.number):
                scopes = [
                    dict(
                        data=Reservation(id=ui.mock_reservation_id(kind), reservation_type=kind, service_name=""),
                        reservation_type=kind,
                    )
                    for kind in ReservationType
                ]
            candidates = chain.from_iterable(
                islice(
                    (message for message in client.sms.list(**scope) if since is None or message.created_at >= since),
                    args.offset + args.limit,
                )
                for scope in scopes
            )
            messages = sorted(_unique(candidates), key=lambda message: message.created_at, reverse=True)[
                args.offset : args.offset + args.limit
            ]
        if messages:
            _display(messages)
        else:
            _notice("No SMS matches these filters.")
        return 0

    since = (
        _timestamp(args.since)
        if args.since
        else (
            datetime(1970, 1, 1, tzinfo=timezone.utc)
            if client.test_mode == TestMode.MOCK_SUCCESS
            else datetime.now(timezone.utc)
        )
    )
    deadline = time.monotonic() + args.timeout if args.timeout >= 0 else float("inf")
    seen = set()
    received = False
    if ui.interactive_output() and not ui.ANIMATE:
        ui.console.print(Text("Waiting for SMS; ctrl-c to stop"))
    while time.monotonic() < deadline:
        timeout = deadline - time.monotonic() if args.timeout >= 0 else -1
        with ui.spinner("waiting for SMS; ctrl-c to stop"):
            incoming = list(
                client.sms.incoming(
                    **_filters(client, args),
                    since=since,
                    timeout=timeout,
                    polling_interval=args.interval,
                )
            )
        batch = []
        for message in incoming:
            if message.id not in seen and message.created_at >= since:
                seen.add(message.id)
                batch.append(message)
        if batch:
            _display(batch)
            received = True
            if not args.follow:
                return 0
        elif not incoming:
            break
    if not received:
        _notice("No new SMS before the timeout.")
        return 1
    return 0


def add_parsers(sub):
    for name, help_text in (("inbox", "unified SMS inbox"), ("poll", "wait for incoming SMS")):
        parser = sub.add_parser(name, help=help_text)
        scope = parser.add_mutually_exclusive_group()
        scope.add_argument("--reservation-id", "--line-id", dest="reservation_id", help="exact reservation/line ID")
        scope.add_argument("--number", "--line-number", dest="number", help="destination phone number")
        parser.add_argument("--type", choices=[kind.value for kind in ReservationType], help="reservation type filter")
        parser.add_argument("--since", help="ISO 8601 timestamp; UTC if no timezone")
        if name == "inbox":
            parser.add_argument("--limit", type=_positive_int, default=5, help="maximum recent messages (default: 5)")
            parser.add_argument("--offset", type=_nonnegative_int, default=0, help="messages to skip (default: 0)")
        else:
            parser.add_argument(
                "--timeout", type=_timeout, default=60, help="seconds to wait; -1 waits indefinitely (default: 60)"
            )
            parser.add_argument(
                "--interval",
                type=_positive_float,
                default=ui.POLL_SECONDS,
                help="poll interval in seconds (default: 3)",
            )
            parser.add_argument("--follow", action="store_true", help="keep streaming until timeout or ctrl-c")


def _nonnegative_int(value):
    import argparse

    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return number


def _positive_int(value):
    import argparse

    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def _positive_float(value):
    import argparse
    import math

    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


def _timeout(value):
    import argparse
    import math

    number = float(value)
    if not math.isfinite(number) or (number < 0 and number != -1):
        raise argparse.ArgumentTypeError("must be nonnegative or -1")
    return number
