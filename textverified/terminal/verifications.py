"""Manage existing verifications using the SDK."""
from itertools import islice

from rich.table import Table
from rich.text import Text
from textverified import TestMode
from . import cli as ui
from .messages import _positive_int, _nonnegative_int


def _display(orders):
    headings = ("ID", "Number", "Service", "State", "Created")
    rows = [(o.id, o.number, o.service_name, o.state.value, ui.local_timestamp(o.created_at)) for o in orders]
    if not ui.interactive_output():
        ui.write_records(headings, rows)
        return
    table = Table(header_style=ui.brand.CYAN, border_style=ui.brand.BRAND)
    for name in headings[1:]:
        table.add_column(name, overflow="fold", no_wrap=name in ("Number", "Created"))
    for order, row in zip(orders, rows):
        table.add_row(
            Text(row[1]), Text(row[2]), Text(order.state.name.split("_", 1)[-1].lower().replace("_", " ")), Text(row[4])
        )
    ui.console.print(table)


def run(client, args):
    command = args.verification_command or "list"
    mock = client.test_mode == TestMode.MOCK_SUCCESS
    if command == "list":
        orders = (
            [client.verifications.details(ui.mock_reservation_id())]
            if mock
            else list(islice(client.verifications.list(), args.offset + args.limit))
        )
        orders.sort(key=lambda order: order.created_at, reverse=True)
        orders = orders[args.offset : args.offset + args.limit]
        if orders:
            _display(orders)
        else:
            if ui.interactive_output():
                ui.status("info", "No verifications.")
            else:
                print("No verifications.", file=ui.sys.stderr)
        return 0
    identifier = args.id
    if mock and (not identifier or not identifier.startswith("mock_")):
        identifier = ui.mock_reservation_id()
    if not identifier:
        raise ValueError("A verification ID is required without --mock.")
    order = client.verifications.details(identifier)
    if command == "show":
        _display([order])
        if ui.interactive_output():
            ui.console.print(Text(f"ID: {order.id}"))
            ui.console.print(
                Text(f"Expires: {ui.local_timestamp(order.ends_at)} | Can cancel: {order.cancel.can_cancel}")
            )
        return 0
    if command == "resume":
        return ui._wait_live(client, order) if ui.interactive_output() else ui._wait_plain(client, order)
    if not order.cancel.can_cancel:
        raise ValueError("The API does not currently allow cancellation of this verification.")
    if not ui.confirm(args, f"Cancel verification {identifier}?"):
        return 2 if not ui.sys.stdin.isatty() else 1
    client.verifications.cancel(order)
    ui.status("ok", "Verification cancelled.")
    return 0


def add_parsers(sub):
    parser = sub.add_parser("verifications", help="list, inspect, cancel or resume verifications")
    parser.set_defaults(limit=5, offset=0)
    commands = parser.add_subparsers(dest="verification_command", metavar="action")
    listing = commands.add_parser("list", help="list existing verifications")
    listing.add_argument("--limit", type=_positive_int, default=5, help="maximum recent verifications (default: 5)")
    listing.add_argument("--offset", type=_nonnegative_int, default=0, help="verifications to skip (default: 0)")
    for name in ("show", "cancel", "resume"):
        action = commands.add_parser(name, help=f"{name} an existing verification")
        action.add_argument("id", nargs="?", help="verification ID; optional with --mock")
        if name == "cancel":
            action.add_argument("--yes", "-y", action="store_true")
