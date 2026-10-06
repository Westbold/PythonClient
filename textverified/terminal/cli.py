"""`tv`: Textverified from the command line.

Everything prints inline, in the scrollback, like any other command. The one
moving part is the badge while a verification waits for its code; when the
output is not a terminal, that becomes plain status lines and the bare code.
"""

from __future__ import annotations

import argparse
import base64
import difflib
import getpass
import os
import sys
import time
import csv
import io
from contextlib import contextmanager, nullcontext
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

from . import __version__, brand, credentials
import requests
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from textverified import (
    TextVerified,
    TextVerifiedError,
    TestMode,
    Service,
    VerificationExpanded,
    Reservation,
    ReservationType,
    NumberType,
    ReservationCapability,
)

POLL_SECONDS = 3


def _client(mock=False, login_credentials=None) -> TextVerified:
    pair = login_credentials or credentials.load()[0]
    if not pair:
        raise ValueError("Not signed in. Run `tv login`, or set TEXTVERIFIED_API_USERNAME and TEXTVERIFIED_API_KEY.")
    user, key = pair
    client = TextVerified(
        api_username=user,
        api_key=key,
        test_mode=TestMode.MOCK_SUCCESS if mock else TestMode.LIVE,
        user_agent=f"TextVerified-Python-TUI/{__version__}",
    )
    # Keep purchase retry policy local to the terminal app.
    client.session.mount("https://", HTTPAdapter(max_retries=0))
    client.session.mount("http://", HTTPAdapter(max_retries=0))
    request = client.session.request

    def timed_request(*args, **kwargs):
        kwargs.setdefault("timeout", 15)
        return request(*args, **kwargs)

    client.session.request = timed_request
    return client


def mock_reservation_id(kind=ReservationType.VERIFICATION, *, expired=False):
    if kind == ReservationType.VERIFICATION:
        return "mock_ver_success"
    prefix = "ren" if kind == ReservationType.RENEWABLE else "nonren"
    return f"mock_{prefix}{'_expired' if expired else ''}_30d"


def _services(
    client: TextVerified, reservation_type=ReservationType.VERIFICATION, number_type=NumberType.MOBILE
) -> list[Service]:
    services = client.services.list(number_type=number_type, reservation_type=reservation_type)
    return sorted({(s.service_name, s.capability): s for s in services}.values(), key=lambda s: s.service_name)


def _price(client: TextVerified, service: str, *, area_code=False, carrier=False) -> float:
    return client.verifications.pricing(
        service_name=service,
        area_code=area_code,
        carrier=carrier,
        number_type=NumberType.MOBILE,
        capability=ReservationCapability.SMS,
    ).price


def _seconds_left(order: VerificationExpanded) -> int:
    ends = order.ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    return max(0, int((ends - datetime.now(timezone.utc)).total_seconds()))


def _codes(client: TextVerified, order: VerificationExpanded) -> list[str]:
    reservation = Reservation(
        id=order.id, reservation_type=ReservationType.VERIFICATION, service_name=order.service_name
    )
    return [
        sms.parsed_code
        for sms in client.sms.list(reservation, reservation_type=ReservationType.VERIFICATION)
        if sms.parsed_code
    ]


console = Console(highlight=False)
ANIMATE = True


def _error_text(error: Exception) -> str:
    if isinstance(error, TextVerifiedError):
        return error.error_description or error.error_code
    if isinstance(error, requests.HTTPError):
        return str(error).splitlines()[0]
    return str(error)


def status(kind: str, *parts) -> None:
    if not interactive_output():
        if kind == "fail":
            print(Text.assemble(*parts).plain, file=sys.stderr)
        else:
            console.print(Text.assemble(*parts))
        return
    tag, colour = brand.BADGES[kind]
    console.print(Text.assemble((tag, f"bold {colour}"), " ", *parts))


def mode_tag(client: TextVerified) -> Text:
    mock = client.test_mode == TestMode.MOCK_SUCCESS
    return Text.assemble(
        ("* ", brand.GOLD if mock else brand.OK), ("mock" if mock else "live", brand.GOLD if mock else brand.OK)
    )


def copy_osc52(value: str) -> bool:
    """Copy through the terminal itself; works over SSH in most terminals."""
    if not sys.stdout.isatty():
        return False
    sys.stdout.write(f"\033]52;c;{base64.b64encode(value.encode()).decode()}\a")
    sys.stdout.flush()
    return True


def logo_line(*parts) -> None:
    """Compact brand line with a braille mark."""
    mark = [(brand.inline_mark(), brand.CYAN), "  "] if interactive_output() else []
    console.print(Text.assemble(*mark, *parts))


def side_by_side(art: Text, lines: list[Text]) -> Table:
    """The badge on the left, a few lines of text beside it, centred on it."""
    grid = Table.grid(padding=(0, 3))
    grid.add_column(no_wrap=True)
    grid.add_column(vertical="middle")
    grid.add_row(art, Group(*lines))
    return grid


class _Spin:
    """The inline mark, dancing, beside a label."""

    def __init__(self, label: str) -> None:
        self.label, self.started = label, time.monotonic()

    def __rich__(self) -> Text:
        t = time.monotonic() - self.started
        return Text.assemble((brand.inline_mark(t if ANIMATE else None), brand.CYAN), "  ", (self.label, brand.DIM))


def confirm(args, prompt):
    if args.yes:
        return True
    if not sys.stdin.isatty():
        status("fail", "Confirmation requires a terminal; pass --yes.")
        return False
    return _ask(Text(prompt + " [y/N] ", style="bold"), default="n") in ("y", "yes")


def write_records(headings, rows):
    buffer = io.StringIO()
    csv.writer(buffer, delimiter="\t", lineterminator="\n").writerows([headings, *rows])
    console.file.write(buffer.getvalue())
    console.file.flush()


def local_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local = value.astimezone()
    return local.strftime("%Y-%m-%d %H:%M %Z") if interactive_output() else local.isoformat(sep=" ", timespec="seconds")


@contextmanager
def purchase(client, kind):
    """Track purchase acceptance without changing the SDK's request workflow."""
    request = client.session.request
    accepted = False
    attempted = False
    recovery = None
    endpoint = "/api/pub/v2/verifications" if kind == "verification" else "/api/pub/v2/reservations/rental"

    def track(method, url, **kwargs):
        nonlocal accepted, attempted, recovery
        is_purchase = method.upper() == "POST" and urlparse(url).path == endpoint
        if is_purchase:
            attempted = True
        response = request(method, url, **kwargs)
        if is_purchase and response.ok:
            accepted = True
            data = response.json()
            if isinstance(data, dict):
                recovery = data.get("href")
        return response

    client.session.request = track
    try:
        yield
    except (TextVerifiedError, requests.RequestException, ValueError) as error:
        if accepted:
            identifier = urlparse(recovery).path.rstrip("/").split("/")[-1] if recovery else None
            command = (
                f"tv verifications show {identifier}" if kind == "verification" else f"tv rentals sale {identifier}"
            )
            hint = f" Recover with `{command}`." if identifier else " Inspect your account's reservations or sales."
            raise ValueError(
                f"Purchase accepted, but details could not be loaded: {_error_text(error)}.{hint} Do not repeat the purchase."
            ) from error
        if attempted and isinstance(error, requests.RequestException):
            raise ValueError(
                f"Purchase outcome is unknown: {_error_text(error)}. Inspect your account before retrying."
            ) from error
        raise
    finally:
        client.session.request = request


def interactive_output() -> bool:
    """Color overrides must not turn a redirected stream into an interactive terminal."""
    return sys.stdout.isatty()


def spinner(label: str):
    """For short waits. Transient: it leaves nothing in the scrollback."""
    if not interactive_output() or not ANIMATE:
        return nullcontext()
    return Live(_Spin(label), console=console, transient=True, refresh_per_second=20, redirect_stdout=False)


def pick_service(
    client: TextVerified, query: str, reservation_type=ReservationType.VERIFICATION, number_type=NumberType.MOBILE
) -> Service:
    with spinner("finding services"):
        services = [
            s
            for s in _services(client, reservation_type, number_type)
            if s.capability in (ReservationCapability.SMS, ReservationCapability.SMS_AND_VOICE_COMBO)
        ]
    by_name = {s.service_name.lower(): s for s in services}
    services = list(by_name.values())
    query = query.strip().lower()
    if query in by_name:
        return by_name[query]

    matches = [s for s in services if query in s.service_name.lower()]
    if len(matches) == 1:
        status("info", "using ", (matches[0].service_name, f"bold {brand.CYAN}"))
        return matches[0]
    if not matches:
        close = difflib.get_close_matches(query, list(by_name), n=3)
        hint = f" Did you mean {', '.join(close)}?" if close else " Try `tv services` to browse."
        raise ValueError(f"No service matches {query!r}.{hint}")

    shown = matches[:9]
    console.print(Text(f"{len(matches)} services match {query!r}:", style=brand.DIM))
    for i, service in enumerate(shown, 1):
        console.print(Text.assemble((f"  {i}  ", brand.CYAN), service.service_name))
    if len(matches) > len(shown):
        console.print(Text(f"  ... and {len(matches) - len(shown)} more; be more specific", style=brand.DIM))
    if not sys.stdin.isatty():
        raise ValueError("Several services match; name one exactly.")
    answer = console.input(Text.assemble(("Which one? ", "bold"), (f"[1-{len(shown)}] ", brand.DIM))).strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(shown):
        raise ValueError("Nothing chosen.")
    return shown[int(answer) - 1]


def cmd_home(client: TextVerified, args: argparse.Namespace) -> int:
    """`tv` on its own: the logo, the account, and what you can do."""
    if client is None:
        who = Text.assemble(
            ("o ", brand.DIM), ("not signed in", brand.DIM), ("   run ", brand.DIM), ("tv login", "bold")
        )
    else:
        try:
            with spinner("signing in"):
                account = client.account.me()
            who = Text.assemble(
                mode_tag(client),
                ("   ", ""),
                (account.username, brand.DIM),
                ("   ", ""),
                (f"{account.current_balance:.2f}", "bold"),
                (" credits", brand.DIM),
            )
        except (TextVerifiedError, requests.RequestException, ValueError) as error:
            who = Text.assemble(mode_tag(client), ("   ", ""), (_error_text(error), brand.DANGER))

    console.print()
    tagline = Text("sms verification, from your terminal", style=brand.DIM)
    console.print(side_by_side(brand.badge(), [Text("textverified", style="bold"), tagline, Text(), who]))

    console.print()
    usage = Table.grid(padding=(0, 3))
    usage.add_column(style=f"bold {brand.INK}")
    usage.add_column(style=brand.DIM)
    for command, purpose in (
        ("tv login", "save your API key, once"),
        ("tv verify <service>", "buy a number and wait for the code"),
        ("tv verifications", "inspect, resume or cancel existing verifications"),
        ("tv services [search]", "find a service and its price"),
        ("tv balance", "show your credits"),
        ("tv inbox", "SMS across all lines and verifications"),
        ("tv poll", "wait for incoming SMS"),
        ("tv rentals", "list and manage rental lines"),
    ):
        usage.add_row(Text(command), Text(purpose))  # Text, so [search] isn't read as markup
    console.print(usage)
    console.print(Text("\nadd --mock to use a server-backed mock verification", style=brand.DIM))
    console.print()
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    """Check the Email and API key, then save in the local credential cache."""
    if not sys.stdin.isatty():
        status(
            "fail", "`tv login` needs a terminal. In scripts, set TEXTVERIFIED_API_USERNAME and TEXTVERIFIED_API_KEY."
        )
        return 2
    logo_line(("login", "bold"), ("   your API key is on your Textverified profile page", brand.DIM))
    if args.email:
        user = args.email.strip()
        console.print(Text.assemble(("Email: ", "bold"), user))
    else:
        user = console.input(Text.assemble(("Email: ", "bold"))).strip()
    key = ""
    for _ in range(3):  # an empty entry is usually an early Enter or an empty clipboard
        try:
            key = getpass.getpass("API key (hidden): ").strip()
        except EOFError:  # ctrl-d
            key = ""
        if key:
            break
        console.print(Text("Nothing was entered. Paste the key, then press Enter (ctrl-c to stop).", style=brand.DIM))
    if not user or not key:
        status("fail", "Nothing saved.")
        return 1
    client = _client(login_credentials=(user, key))
    try:
        with spinner("checking your key"):
            account = client.account.me()
    finally:
        client.session.close()
    credentials.save(user, key)
    status(
        "ok",
        "Signed in as ",
        (account.username, "bold"),
        ("  |  ", brand.DIM),
        (f"{account.current_balance:.2f}", "bold"),
        (" credits", brand.DIM),
    )
    console.print(Text("         saved in your local credential cache; `tv logout` removes it", style=brand.DIM))
    if credentials.from_environment():
        console.print(
            Text("         note: TEXTVERIFIED_* environment variables are set and take precedence", style=brand.GOLD)
        )
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    if credentials.clear():
        status("ok", "Signed out; credentials removed from the local cache.")
    else:
        status("info", "No saved credentials.")
    if credentials.from_environment():
        console.print(
            Text("         TEXTVERIFIED_* environment variables are still set in this shell", style=brand.GOLD)
        )
    return 0


def cmd_balance(client: TextVerified, args: argparse.Namespace) -> int:
    with spinner("checking your balance"):
        account = client.account.me()
    logo_line(
        (f"{account.current_balance:.2f}", "bold"),
        (" credits", brand.DIM),
        ("   ", ""),
        (account.username, brand.DIM),
        ("   ", ""),
        mode_tag(client),
    )
    return 0


def _price_or_none(client: TextVerified, service: Service) -> float | None:
    try:
        return (
            _price(client, service.service_name)
            if service.capability in (ReservationCapability.SMS, ReservationCapability.SMS_AND_VOICE_COMBO)
            else None
        )
    except (TextVerifiedError, requests.RequestException, ValueError):
        return None


def cmd_services(client: TextVerified, args: argparse.Namespace) -> int:
    query = (args.query or "").lower()
    with spinner("finding services"):
        kind = ReservationType(args.kind) if getattr(args, "kind", None) else ReservationType.VERIFICATION
        number_type = NumberType(getattr(args, "number_type", "mobile"))
        found = [s for s in _services(client, kind, number_type) if query in s.service_name.lower()]
    if not found:
        if interactive_output():
            status("info", f"No services match {args.query!r}")
        else:
            print(f"No services match {args.query!r}", file=sys.stderr)
        return 1

    # Prices are one request each, so they're fetched only for a short list.
    total = len(found)
    found = found[args.offset : args.offset + args.limit]
    if not found:
        message = f"No matching services at offset {args.offset}."
        if interactive_output():
            status("info", message)
        else:
            print(message, file=sys.stderr)
        return 0
    prices: dict[str, float] = {}
    if len(found) <= 24 and kind == ReservationType.VERIFICATION:
        with spinner("checking prices"), ThreadPoolExecutor(8) as pool:
            for service, price in zip(found, pool.map(lambda s: _price_or_none(client, s), found), strict=True):
                if price is not None:
                    prices[service.service_name] = price

    count = f"{len(found)} of {total} service{'s' if total != 1 else ''}"
    if not interactive_output():
        write_records(
            ("Service", "Capability", "Price"),
            [
                (
                    s.service_name,
                    s.capability.value,
                    f"{prices[s.service_name]:.2f}" if s.service_name in prices else "",
                )
                for s in found
            ],
        )
        if total > len(found):
            print(
                f"Showing {len(found)} of {total} services (offset {args.offset}); use --offset N --limit N or narrow the search.",
                file=sys.stderr,
            )
        return 0
    logo_line(
        (count, "bold"), (f" matching {args.query!r}" if args.query else "", brand.DIM), ("   ", ""), mode_tag(client)
    )
    table = Table.grid(padding=(0, 3))
    table.add_column(style=brand.INK, no_wrap=True)
    table.add_column(style=brand.DIM)
    table.add_column(style=brand.GOLD, justify="right")
    for service in found:
        price = prices.get(service.service_name)
        table.add_row(service.service_name, service.capability.value, f"{price:.2f}" if price is not None else "")
    console.print(table)
    if total > len(found):
        console.print(
            Text(
                f"Showing {len(found)} of {total} services (offset {args.offset}); use --offset N --limit N or narrow the search.",
                style=brand.DIM,
            )
        )
    return 0


def cmd_verify(client: TextVerified, args: argparse.Namespace) -> int:
    logo_line(("verify", "bold"), (f" {args.service}", brand.DIM), ("   ", ""), mode_tag(client))
    service = pick_service(client, args.service)
    with spinner("pricing"):
        price = _price(client, service.service_name, area_code=bool(args.area_code), carrier=bool(args.carrier))
        account = client.account.me()
    status(
        "info",
        (service.service_name, f"bold {brand.CYAN}"),
        (" | SMS verification | ", brand.DIM),
        (f"{price:.2f} credits", brand.GOLD),
        (f"  (balance {account.current_balance:.2f})", brand.DIM),
    )

    prompt = "Create this mock verification?" if client.test_mode == TestMode.MOCK_SUCCESS else "Buy this number?"
    if not confirm(args, prompt):
        return 2 if not sys.stdin.isatty() else 1

    with spinner("reserving a number"), purchase(client, "verification"):
        order = client.verifications.create(
            service_name=service.service_name,
            capability=ReservationCapability.SMS,
            max_price=price,
            area_code_select_option=args.area_code,
            carrier_select_option=args.carrier,
        )
    status("ok", "Reserved ", (order.number, "bold"), (f" | {order.total_cost:.2f} credits", brand.DIM))
    status("info", f"Verification ID: {order.id}")

    if not interactive_output():
        return _wait_plain(client, order)
    return _wait_live(client, order)


def _card(order: VerificationExpanded, art: Text, headline: Text, detail: Text, foot: Text) -> Table:
    return side_by_side(
        art,
        [
            Text.assemble((order.service_name, f"bold {brand.CYAN}"), ("  |  ", brand.DIM), headline),
            Text(order.number, style="bold"),
            detail,
            foot,
        ],
    )


def _wait_live(client: TextVerified, order: VerificationExpanded) -> int:
    """The badge dances until the code arrives, then becomes the logo."""
    started = time.monotonic()
    console.print()
    with Live(console=console, refresh_per_second=20, transient=False, redirect_stdout=False) as live:
        next_poll = 0.0
        while True:
            try:
                now = time.monotonic()
                left = _seconds_left(order)
                clock = Text(f"{left // 60}:{left % 60:02d}", style=brand.GOLD if left < 60 else brand.DIM)
                live.update(
                    _card(
                        order,
                        brand.dancing(now - started) if ANIMATE else brand.waiting_still(),
                        Text("waiting for the SMS", style=brand.INK),
                        Text.assemble(("expires in ", brand.DIM), clock),
                        Text("enter the number on the site | ctrl-c to cancel", style=brand.DIM),
                    )
                )
                if left == 0:
                    live.update(
                        _card(
                            order,
                            brand.stopped(),
                            Text("expired", style=brand.DANGER),
                            Text("no SMS arrived", style=brand.DIM),
                            Text("unused verifications are refunded automatically", style=brand.DIM),
                        )
                    )
                    return 1
                if now >= next_poll:
                    next_poll = now + POLL_SECONDS
                    codes = _codes(client, order)
                    if codes:
                        return _land(live, order, codes[-1], now - started)
                time.sleep(0.05)
            except KeyboardInterrupt:
                live.update(Text(""))
                live.stop()
                if _confirm_cancel(client, order):
                    console.print()
                    return 130
                live.start()


def _land(live: Live, order: VerificationExpanded, code: str, took: float) -> int:
    copied = copy_osc52(code)
    spaced = " ".join(code)
    foot = Text(
        ("copied to clipboard | " if copied else "") + f"took {int(took) // 60}:{int(took) % 60:02d}", style=brand.DIM
    )
    frames = 19 if ANIMATE else 1
    for step in range(frames):
        live.update(
            _card(
                order,
                brand.settling(step / (frames - 1)) if ANIMATE else brand.badge(),
                Text("verified", style=f"bold {brand.OK}"),
                Text(spaced, style=f"bold {brand.CYAN}"),
                foot,
            )
        )
        time.sleep(0.05 if ANIMATE else 0)
    console.print()
    return 0


def _confirm_cancel(client: TextVerified, order: VerificationExpanded) -> bool:
    """Ctrl-c while waiting. Returns True if tv should stop waiting.

    Textverified doesn't allow every verification to be cancelled at every
    moment, so ask the API first rather than promise a refund it won't give.
    """
    console.print()
    can_cancel = order.cancel.can_cancel
    try:
        with spinner("checking"):
            order = client.verifications.details(order)
            can_cancel = order.cancel.can_cancel
    except (TextVerifiedError, requests.RequestException, ValueError) as error:
        status("fail", _error_text(error))
        can_cancel = True  # unknown: let the cancel request decide

    if can_cancel:
        prompt = Text.assemble(
            ("Cancel this verification? ", "bold"),
            (f"{order.total_cost:.2f} credits back ", brand.DIM),
            ("[Y/n] ", brand.DIM),
        )
        if _ask(prompt, default="y") in ("y", "yes"):
            try:
                with spinner("cancelling"):
                    client.verifications.cancel(order)
                status("ok", "Verification cancelled.")
                return True
            except (TextVerifiedError, requests.RequestException, ValueError) as error:
                status("fail", _error_text(error))
                can_cancel = False  # fall through to the options below
        else:
            console.print(Text("Still waiting...", style=brand.DIM))
            return False

    left = _seconds_left(order)
    console.print(
        Text.assemble(
            ("Textverified won't cancel this one right now. ", brand.INK),
            (f"It expires in {left // 60}:{left % 60:02d}; ", brand.DIM),
            ("if no code arrives, the credits are refunded automatically.", brand.DIM),
        )
    )
    choice = _ask(Text.assemble(("Keep waiting, or leave it? ", "bold"), ("[W/l] ", brand.DIM)), default="w")
    if choice in ("l", "leave", "q"):
        status("info", "Left running: ", (order.number, "bold"), (f" for {order.service_name}", brand.DIM))
        return True
    console.print(Text("Still waiting...", style=brand.DIM))
    return False


def _ask(prompt: Text, default: str) -> str:
    try:
        return console.input(prompt).strip().lower() or default
    except (KeyboardInterrupt, EOFError):
        return default


def _wait_plain(client: TextVerified, order: VerificationExpanded) -> int:
    status("wait", "Waiting for SMS")
    while _seconds_left(order) > 0:
        codes = _codes(client, order)
        if codes:
            code = codes[-1]
            print(code)  # last line, bare, for scripts
            return 0
        time.sleep(POLL_SECONDS)
    status("fail", "No SMS before the number expired. Unused verifications are refunded automatically.")
    return 1


def main(argv: list[str] | None = None) -> int:
    global ANIMATE, console
    parser = argparse.ArgumentParser(prog="tv", description="Textverified from your terminal.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="use SDK mock scenarios and server-backed mock resources (requires login)",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        default=bool(os.environ.get("TV_NO_ANIMATION")),
        help="keep the badge still",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="ANSI colors: auto detects a terminal (default); always forces terminal colors; never disables colors; pipes stay plain",
    )
    parser.add_argument("--version", action="version", version=f"tv {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")
    login = sub.add_parser("login", help="check Email and API key, then save in the local cache")
    login.add_argument("--email", help="your Textverified login email (asked for if left out)")
    sub.add_parser("logout", help="remove saved credentials")
    sub.add_parser("balance", help="show your credits")
    services = sub.add_parser("services", help="find services; prices for short lists")
    services.add_argument("query", nargs="?")
    verify = sub.add_parser("verify", help="buy a number and wait for the code")
    verify.add_argument("service", help="service name, or part of one")
    verify.add_argument("--area-code", action="append", help="preferred area code; repeat for more")
    verify.add_argument("--carrier", action="append", help="preferred carrier; repeat for more")
    verify.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    from . import messages, rentals, verifications

    services.add_argument("--limit", type=messages._positive_int, default=5, help="maximum services (default: 5)")
    services.add_argument(
        "--offset", type=messages._nonnegative_int, default=0, help="matching services to skip (default: 0)"
    )
    messages.add_parsers(sub)
    rentals.add_parsers(sub)
    verifications.add_parsers(sub)
    args = parser.parse_args(argv)
    ANIMATE = not args.no_animation and interactive_output()
    previous_console = console
    terminal = interactive_output()
    if args.color != "auto" or not terminal:
        color = terminal and args.color != "never"
        console = Console(
            file=previous_console.file,
            width=previous_console.width,
            highlight=False,
            force_terminal=True if color else False if not terminal else None,
            color_system="truecolor" if color else None,
            no_color=not color,
        )

    client = None
    try:
        if args.command in ("login", "logout"):
            return {"login": cmd_login, "logout": cmd_logout}[args.command](args)
        if args.command is None and not credentials.load()[0]:
            return cmd_home(None, args)  # signed out: still show the home screen
        client = _client(mock=args.mock)
        command = {
            None: cmd_home,
            "balance": cmd_balance,
            "services": cmd_services,
            "verify": cmd_verify,
            "inbox": messages.run,
            "poll": messages.run,
            "rentals": rentals.run,
            "verifications": verifications.run,
        }[args.command]
        return command(client, args)
    except (TextVerifiedError, requests.RequestException, ValueError, credentials.CredentialError) as error:
        status("fail", _error_text(error))
        return 1
    except KeyboardInterrupt:
        if interactive_output():
            console.print()
        return 130
    finally:
        console = previous_console
        if client is not None:
            client.session.close()


if __name__ == "__main__":
    sys.exit(main())
