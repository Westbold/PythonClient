"""Rental commands using the SDK's generated records."""
from itertools import islice
from concurrent.futures import ThreadPoolExecutor
from rich.table import Table
from rich.text import Text
from textverified import (
    RentalDuration,
    ReservationType,
    NumberType,
    ReservationCapability,
    TestMode,
    RenewableRentalExpanded,
)
from . import cli as ui
from .messages import _positive_int, _nonnegative_int


def _table(rentals):
    headings = ("ID", "Number", "Service", "Type", "State", "Created")
    rows = [
        (r.id, r.number, r.service_name, kind, r.state.value, ui.local_timestamp(r.created_at)) for kind, r in rentals
    ]
    if not ui.interactive_output():
        ui.write_records(
            headings,
            rows,
        )
        return
    table = Table(header_style=ui.brand.CYAN, border_style=ui.brand.BRAND)
    for name in headings[1:]:
        table.add_column(name, overflow="fold", no_wrap=name in ("Number", "Created"))
    for (_, rental), row in zip(rentals, rows):
        table.add_row(
            Text(row[1]),
            Text(row[2]),
            Text(row[3]),
            Text(rental.state.name.split("_", 1)[-1].lower().replace("_", " ")),
            Text(row[5]),
        )
    ui.console.print(table)


def _details(rental):
    kind = "renewable" if isinstance(rental, RenewableRentalExpanded) else "nonrenewable"
    _table([(kind, rental)])
    if not ui.interactive_output():
        return
    ui.console.print(Text(f"ID: {rental.id} | Always on: {'yes' if rental.always_on else 'no'}"))
    if rental.ends_at:
        ui.console.print(Text("Expires: " + ui.local_timestamp(rental.ends_at), style=ui.brand.DIM))
    if kind == "renewable":
        ui.console.print(
            Text(
                f"Billing cycle: {rental.billing_cycle_id} | Included for renewal: {rental.is_included_for_next_renewal}",
                style=ui.brand.DIM,
            )
        )


def _configuration(client, args):
    kind = ReservationType(args.kind)
    number_type = NumberType(args.number_type)
    service = ui.pick_service(client, args.service, kind, number_type)
    return dict(
        service_name=service.service_name,
        duration=RentalDuration(args.duration),
        is_renewable=kind == ReservationType.RENEWABLE,
        always_on=args.always_on,
        number_type=number_type,
        capability=ReservationCapability.SMS,
        area_code_select_option=args.area_code,
        billing_cycle_id_to_assign_to=args.billing_cycle,
        allow_back_order_reservations=args.backorder,
    )


def run(client, args):
    api = client.reservations
    command = args.rental_command or "list"
    if client.test_mode == TestMode.MOCK_SUCCESS and hasattr(args, "id") and command != "sale":
        if not args.id or not args.id.startswith("mock_"):
            if command == "backorder":
                args.id = "mock_bo_success"
            else:
                kind = args.kind or ("nonrenewable" if command == "extend" else "renewable")
                args.id = ui.mock_reservation_id(ReservationType(kind), expired=command in ("reactivate", "renew"))
    if hasattr(args, "id") and not args.id:
        raise ValueError("A reservation or backorder ID is required without --mock.")
    if command == "list":
        kinds = [args.kind] if args.kind else ["renewable", "nonrenewable"]

        def recent(kind):
            if client.test_mode == TestMode.MOCK_SUCCESS:
                rental = getattr(api, kind + "_details")(ui.mock_reservation_id(ReservationType(kind)))
                return [(kind, rental)]
            return [(kind, rental) for rental in islice(getattr(api, "list_" + kind)(), args.offset + args.limit)]

        with ui.spinner("loading recent rentals"):
            if len(kinds) == 1:
                found = recent(kinds[0])
            else:
                client.refresh_bearer()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    found = [row for batch in pool.map(recent, kinds) for row in batch]
        found.sort(key=lambda row: row[1].created_at, reverse=True)
        found = found[args.offset : args.offset + args.limit]
        if found:
            _table(found)
        else:
            if ui.interactive_output():
                ui.status("info", "No rentals.")
            else:
                print("No rentals.", file=ui.sys.stderr)
        return 0
    if command == "services":
        return ui.cmd_services(client, args)
    if command == "show":
        rental = api.details(args.id)
        if rental is None:
            raise ValueError("No rental details returned for this ID.")
        _details(rental)
        return 0
    if command == "sale":
        sale = client.sales.get(args.id)
        ui.status("info", f"Sale {sale.id} | {sale.state.value} | {sale.total:.2f} credits")
        _sale_details(client, sale)
        return 0
    if command == "backorder":
        backorder = api.backorder(args.id)
        ui.status("info", f"Backorder {backorder.id} | {backorder.service_name} | {backorder.status.value}")
        ui.console.print(Text(f"Sale: {backorder.sale_id} | Reservation: {backorder.reservation_id or 'not assigned'}"))
        return 0
    if command == "health":
        health = api.check_health(args.id)
        ui.status(
            "info",
            f"Line {health.line_number} | Checked: {health.checked_at.isoformat() if health.checked_at else 'not checked'}",
        )
        return 0
    if command == "notes":
        notes = api.user_notes(args.id)
        ui.console.print(Text(notes.user_notes or "No notes."))
        return 0
    if command in ("price", "buy"):
        configuration = _configuration(client, args)
        price = api.pricing(
            service_name=configuration["service_name"],
            duration=configuration["duration"],
            is_renewable=configuration["is_renewable"],
            always_on=configuration["always_on"],
            number_type=configuration["number_type"],
            capability=configuration["capability"],
            area_code=bool(args.area_code),
            call_forwarding=False,
            billing_cycle_id_to_assign_to=args.billing_cycle,
        ).price
        ui.status("info", f"{configuration['service_name']} | {args.kind} | {args.duration} | {price:.2f} credits")
        if command == "price":
            return 0
        if not ui.confirm(
            args, "Create this mock rental?" if client.test_mode == TestMode.MOCK_SUCCESS else "Purchase this rental?"
        ):
            return 2 if not ui.sys.stdin.isatty() else 1
        with ui.purchase(client, "rental"):
            sale = api.create(**configuration)
        ui.status("ok", f"Sale {sale.id} | {sale.state.value} | {sale.total:.2f} credits")
        _sale_details(client, sale)
        return 0

    if command == "wake":
        wake = client.wake_requests.create(args.id)
        ui.status("ok", f"Wake request {wake.id} | scheduled: {wake.is_scheduled}")
        if args.wait:
            wake = client.wake_requests.wait_for_wake_request(wake)
        if wake.usage_window_start:
            ui.console.print(
                Text(
                    f"Usage window: {wake.usage_window_start.isoformat()} to {wake.usage_window_end.isoformat() if wake.usage_window_end else 'pending'}"
                )
            )
        return 0
    rental = api.details(args.id)
    if rental is None:
        raise ValueError("No rental details returned for this ID.")
    renewable = isinstance(rental, RenewableRentalExpanded)
    if command == "update":
        options = dict(user_notes=args.notes, tags=args.tags, mark_all_sms_read=True if args.mark_read else None)
        if renewable:
            options["include_for_renewal"] = args.renewal
            api.update_renewable(rental, **options)
        else:
            if args.renewal is not None:
                raise ValueError("Renewal preferences apply only to renewable rentals.")
            api.update_nonrenewable(rental, **options)
        ui.status("ok", "Rental updated.")
        return 0
    if command == "renew" and not renewable:
        raise ValueError("Use rentals extend for a nonrenewable rental.")
    if command == "extend" and renewable:
        raise ValueError("Use rentals renew for an overdue renewable rental.")
    if command == "reactivate":
        price = api.reactivation_cost(rental).price
        ui.status("info", f"Reactivation: {price:.2f} credits")
        if not ui.confirm(args, f"Reactivate rental {args.id} for {price:.2f} credits?"):
            return 2 if not ui.sys.stdin.isatty() else 1
        api.reactivate(rental, max_price=price)
        ui.status("ok", "Rental reactivated.")
        return 0
    if not ui.confirm(args, f"{command.capitalize()} rental {args.id}?"):
        return 2 if not ui.sys.stdin.isatty() else 1
    if command == "renew":
        api.renew_overdue(rental)
    elif command == "extend":
        api.extend_nonrenewable(rental_id=rental.id, extension_duration=RentalDuration(args.duration))
    elif command == "refund":
        (api.refund_renewable if renewable else api.refund_nonrenewable)(rental)
    ui.status("ok", f"Rental {command} request completed.")
    return 0


def _sale_details(client, sale):
    try:
        for reservation in sale.reservations:
            rental = client.reservations.details(reservation)
            if rental is None:
                raise ValueError("No rental details returned.")
            _details(rental)
        for backorder in sale.back_order_reservations:
            ui.status("info", f"Backorder {backorder.id} | {backorder.service_name}")
    except (ui.TextVerifiedError, ui.requests.RequestException, ValueError) as error:
        raise ValueError(
            f"Sale {sale.id} exists, but rental details could not be loaded: {ui._error_text(error)}. Recover with `tv rentals sale {sale.id}`; do not repeat the purchase."
        ) from error


def add_parsers(sub):
    parser = sub.add_parser("rentals", help="list, purchase and manage rentals")
    parser.set_defaults(kind=None, limit=5, offset=0)
    commands = parser.add_subparsers(dest="rental_command", metavar="action")
    listing = commands.add_parser("list", help="list renewable and nonrenewable rentals")
    listing.add_argument("--kind", choices=("renewable", "nonrenewable"))
    listing.add_argument(
        "--limit", type=_positive_int, default=5, help="maximum recent rentals across types (default: 5)"
    )
    listing.add_argument("--offset", type=_nonnegative_int, default=0, help="rentals to skip across types (default: 0)")
    show = commands.add_parser("show", help="rental details")
    show.add_argument("id", nargs="?", help="rental reservation ID; optional with --mock")
    show.add_argument("--kind", choices=("renewable", "nonrenewable"))
    services = commands.add_parser("services", help="search the rental service catalog")
    services.add_argument("query", nargs="?")
    services.add_argument("--limit", type=_positive_int, default=5, help="maximum services (default: 5)")
    services.add_argument("--offset", type=_nonnegative_int, default=0, help="matching services to skip (default: 0)")
    services.add_argument("--kind", choices=("renewable", "nonrenewable"), default="renewable")
    services.add_argument("--number-type", choices=[kind.value for kind in NumberType], default="mobile")
    for name, help_text in (
        ("backorder", "backorder status"),
        ("health", "line health check"),
        ("notes", "show rental notes"),
        ("sale", "recover purchase details by sale ID"),
    ):
        read = commands.add_parser(name, help=help_text)
        read.add_argument("id", nargs="?", help="backorder or rental ID; optional with --mock")
        read.add_argument("--kind", choices=("renewable", "nonrenewable"))
    for name in ("price", "buy"):
        purchase = commands.add_parser(name, help="quote a rental" if name == "price" else "purchase a rental")
        purchase.add_argument("service")
        purchase.add_argument("--kind", choices=("renewable", "nonrenewable"), default="renewable")
        purchase.add_argument(
            "--duration",
            choices=[duration.value for duration in RentalDuration],
            default=RentalDuration.THIRTY_DAY.value,
        )
        purchase.add_argument("--always-on", action="store_true")
        purchase.add_argument("--number-type", choices=[kind.value for kind in NumberType], default="mobile")
        purchase.add_argument("--area-code", action="append", help="allowed area code; repeat for more")
        purchase.add_argument("--billing-cycle", help="existing billing cycle for a renewable rental")
        purchase.add_argument("--backorder", action="store_true", help="allow a backorder if out of stock")
        if name == "buy":
            purchase.add_argument("--yes", "-y", action="store_true", help="skip purchase confirmation")
    for name in ("wake", "renew", "extend", "refund", "reactivate", "update"):
        action = commands.add_parser(
            name,
            help={
                "wake": "wake a sleeping rental",
                "renew": "renew an overdue renewable rental",
                "extend": "extend a nonrenewable rental",
                "refund": "request a rental refund",
                "reactivate": "quote and reactivate an expired rental",
                "update": "change notes, tags or renewal preferences",
            }[name],
        )
        action.add_argument("id", nargs="?", help="rental reservation ID; optional with --mock")
        action.add_argument("--kind", choices=("renewable", "nonrenewable"))
        if name == "wake":
            action.add_argument("--wait", action="store_true", help="wait until the usage window opens")
        elif name == "update":
            action.add_argument("--notes")
            action.add_argument("--tags", nargs="*", help="replacement tags; empty clears all tags")
            action.add_argument("--mark-read", action="store_true")
            renewal = action.add_mutually_exclusive_group()
            renewal.add_argument("--renewal", dest="renewal", action="store_const", const=True, default=None)
            renewal.add_argument("--no-renewal", dest="renewal", action="store_const", const=False)
        else:
            action.add_argument("--yes", "-y", action="store_true", help="skip confirmation")
            if name == "extend":
                action.add_argument(
                    "--duration", choices=[duration.value for duration in RentalDuration], required=True
                )
