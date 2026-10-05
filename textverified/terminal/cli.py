"""Scriptable Typer commands. Textual is imported only by the tui command."""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, List
import typer
import requests
from textverified.exceptions import TextVerifiedError
from .adapter import Adapter
from .application import Application
from .config import Config, TerminalError
from .fields import descriptor, merge_inputs, scalar
from .models import matches, timestamp, safe
from .output import emit, event, finite, ReplaySpool
from .state import State

app = typer.Typer(
    no_args_is_help=False,
    help="TextVerified numbers and account-wide SMS. Install: pip install textverified[tui]",
    pretty_exceptions_enable=False,
)
auth = typer.Typer(help="Manage locally cached account credentials.")
account = typer.Typer()
verification = typer.Typer()
rental = typer.Typer()
sms = typer.Typer()
schema = typer.Typer()
theme = typer.Typer()
config_app = typer.Typer()
for name, group in [
    ("auth", auth),
    ("account", account),
    ("verification", verification),
    ("rental", rental),
    ("sms", sms),
    ("schema", schema),
    ("theme", theme),
    ("config", config_app),
]:
    app.add_typer(group, name=name)


def version_callback(value: bool):
    if value:
        from textverified import __version__

        typer.echo(__version__)
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    profile: Optional[str] = None,
    non_interactive: bool = False,
    color: str = "auto",
    debug: bool = False,
    version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True),
):
    if color not in ("auto", "always", "never"):
        raise ValueError("--color must be auto, always or never")
    ctx.obj = dict(profile=profile, non_interactive=non_interactive, color=color, debug=debug)
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty() and sys.stdout.isatty() and not non_interactive:
            launch_tui(ctx)
        else:
            typer.echo(ctx.get_help())


def context(ctx):
    return ctx.find_root().obj


def workflow(ctx):
    obj = context(ctx)
    if "workflow" not in obj:
        config = Config()
        user, key, profile = config.credentials(obj["profile"])
        adapter = Adapter(user, key, profile, config.settings["sync"]["request_timeout_seconds"])
        obj["workflow"] = Application(adapter, config, State(config))
        ctx.find_root().call_on_close(obj["workflow"].close)
    return obj["workflow"]


def approve(ctx, yes, message):
    if yes:
        return
    if context(ctx)["non_interactive"] or not sys.stdin.isatty():
        raise ValueError("Explicit confirmation required; supply --yes")
    if not typer.confirm(safe(message), default=False):
        raise typer.Exit(2)


@app.command("tui")
def launch_tui(ctx: typer.Context, theme: Optional[str] = None, reset_style: bool = False):
    """Open the full-screen Numbers / Inbox application."""
    if context(ctx)["non_interactive"] or not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("The TUI requires an interactive terminal; use list or sms watch --format ndjson")
    from .tui import TerminalApp

    config = Config()
    if context(ctx)["color"] != "auto":
        config.settings["appearance"]["color"] = context(ctx)["color"]
    try:
        service = workflow(ctx)
    except TerminalError as exc:
        if exc.status != 3:
            raise
        service = None
    TerminalApp(
        service, config=config, profile=context(ctx)["profile"], selected_theme=theme, reset_style=reset_style
    ).run(mouse=config.settings["ui"]["mouse"])


@auth.command("login")
def login(ctx: typer.Context, profile: str = typer.Option("default", "--profile")):
    """Ask for Email and API key, validate and save in the local cache."""
    if context(ctx)["non_interactive"] or not sys.stdin.isatty():
        raise ValueError("Login needs an interactive terminal; use environment credentials for scripts")
    config = Config()
    config.check_profile_name(profile)
    username = typer.prompt("Email").strip()
    key = typer.prompt("API key", hide_input=True)
    adapter = Adapter(username, key, profile)
    try:
        snapshot = adapter.account()
    finally:
        adapter.close()
    config.save_credentials(username, key, profile)
    typer.echo("Saved profile " + profile + " for " + safe(snapshot["username"]))


@auth.command("logout")
def logout(profile: str = typer.Option("default", "--profile")):
    config = Config()
    config.remove_credentials(profile)
    typer.echo("Removed profile " + profile)


@auth.command("status")
def auth_status(ctx: typer.Context):
    service = workflow(ctx)
    snapshot = service.adapter.account()
    emit(dict(schema_version=1, source="profile" if snapshot["profile"] else "environment", account=snapshot))


@account.command("show")
def account_show(ctx: typer.Context, format: str = "table", json_output: bool = typer.Option(False, "--json")):
    snapshot = workflow(ctx).adapter.account()
    if json_output or format == "json":
        emit(dict(schema_version=1, account=snapshot))
    else:
        typer.echo(safe(snapshot["username"]) + " | Balance: " + snapshot["balance_amount"] + " credits")


def list_command(fixed_kind=None):
    def command(
        ctx: typer.Context,
        limit: Optional[int] = None,
        all_history: bool = typer.Option(False, "--all"),
        query: str = "",
        format: str = "table",
        json_output: bool = typer.Option(False, "--json"),
        state: str = "all",
        kind: str = "all",
    ):
        service = workflow(ctx)
        if state not in ("all", "active", "history", "attention") or kind not in ("all", "verification", "rental"):
            raise ValueError("Invalid state or kind")
        count = list_limit(service, limit, all_history)
        rows = service.numbers(fixed_kind or kind)
        records = (r for r in rows if (state == "all" or r["lifecycle"] == state) and matches(r, query))
        finite(
            records,
            service.adapter.account_scope,
            "json" if json_output else format,
            count,
            warnings=getattr(service.adapter, "warnings", []),
        )

    return command


app.command("list")(list_command())
verification.command("list")(list_command("verification"))
rental.command("list")(list_command("rental"))


def get_command(kind):
    def command(ctx: typer.Context, id: str, json_output: bool = typer.Option(False, "--json")):
        record = workflow(ctx).adapter.details(kind, id)
        if json_output:
            emit(dict(schema_version=1, resource=record))
        else:
            typer.echo(safe(json.dumps(record, indent=2)))

    return command


verification.command("get")(get_command("verification"))
rental.command("get")(get_command("rental"))


def list_limit(service, limit, all_history):
    if all_history and limit is not None:
        raise ValueError("--all and --limit are mutually exclusive")
    if limit is not None and limit < 1:
        raise ValueError("--limit must be positive")
    return None if all_history else limit or int(service.config.settings["cli"]["list_limit"])


def sms_filter(number=None, type="all", since=None, before=None, id=None, kind=None, query=""):
    if id:
        if number or kind not in ("verification", "renewable", "nonrenewable"):
            raise ValueError("--id requires --kind and cannot be combined with --number")

    if kind and not id:
        raise ValueError("--kind requires --id")
    if type not in ("all", "unknown", "verification", "renewable", "nonrenewable", "rental"):
        raise ValueError("Invalid SMS type")
    since = timestamp(since, strict=True) if since else None
    before = timestamp(before, strict=True) if before else None

    def accepted(message):
        created = message["created_at"]
        return (
            (not number or message["to_number"] == number)
            and (
                type == "all"
                or message["resource_kind"] == type
                or type == "rental"
                and message["resource_kind"] in ("renewable", "nonrenewable")
            )
            and (not since or created is not None and created >= since)
            and (not before or created is not None and created < before)
            and matches(message, query)
        )

    return accepted


def unique_messages(records):
    seen = set()
    for message in records:
        if message["id"] not in seen:
            seen.add(message["id"])
            yield message


@sms.command("list")
def sms_list(
    ctx: typer.Context,
    limit: Optional[int] = None,
    all_history: bool = typer.Option(False, "--all"),
    query: str = "",
    format: str = "table",
    json_output: bool = typer.Option(False, "--json"),
    number: Optional[str] = None,
    type: str = "all",
    since: Optional[str] = None,
    before: Optional[str] = None,
    id: Optional[str] = None,
    kind: Optional[str] = None,
):
    predicate = sms_filter(number, type, since, before, id, kind, query)
    service = workflow(ctx)
    count = list_limit(service, limit, all_history)
    records = (
        m
        for m in unique_messages(
            service.adapter.messages(
                number=number, resource_id=id, resource_kind=kind or (type if type not in ("all", "unknown") else None)
            )
        )
        if predicate(m)
    )
    warnings = (
        ["SMS resource association is unknown in this API schema", "Timestamp filters exclude unavailable timestamps"]
        if since or before
        else ["SMS resource association is unknown in this API schema"]
    )
    warnings.extend(getattr(service.adapter, "warnings", []))
    if hasattr(service.adapter, "warnings"):
        service.adapter.warnings = warnings
    finite(
        records, service.adapter.account_scope, "json" if json_output else format, count, sms=True, warnings=warnings
    )


def diagnostic(code, message, format, retryable=False):
    if format == "ndjson":
        print(
            json.dumps(dict(schema_version=1, status=dict(code=code, message=message, retryable=retryable))),
            file=sys.stderr,
            flush=True,
        )
    else:
        typer.echo(safe(message), err=True)


def stream_output(service, name, message, format, replay=False):
    if format == "ndjson":
        emit(event(service.adapter.account_scope, name, message, replay))
    else:
        typer.echo(
            safe(
                " | ".join(
                    str(message.get(k) or "") for k in ("created_at", "to_number", "from_number", "body", "parsed_code")
                )
            ),
            nl=True,
        )
        sys.stdout.flush()


@sms.command("watch")
def watch(
    ctx: typer.Context,
    number: Optional[str] = None,
    type: str = "all",
    since: Optional[str] = None,
    before: Optional[str] = None,
    id: Optional[str] = None,
    kind: Optional[str] = None,
    query: str = "",
    tail: Optional[int] = None,
    resume: Optional[str] = None,
    timeout: float = 0,
    format: str = "table",
    json_output: bool = typer.Option(False, "--json"),
):
    if json_output or format not in ("table", "ndjson"):
        raise ValueError("Watch is a stream; use --format ndjson, not --json")
    if timeout < 0 or tail is not None and tail < 0:
        raise ValueError("Timeout and tail must be nonnegative")
    if resume and (tail is not None or since) or since and tail is not None:
        raise ValueError("--resume, --tail and --since are mutually exclusive")
    predicate = sms_filter(number, type, since, before, id, kind, query)
    service = workflow(ctx)
    if tail is not None and tail > service.feed.max_bodies:
        raise ValueError("--tail exceeds the configured message working set; use --since for complete replay")
    filters = json.dumps(dict(number=number, type=type, before=before, query=query, id=id, kind=kind), sort_keys=True)
    resumed = service.state.checkpoint(service.adapter.scope, resume, filters) if resume else None
    if resumed is not None:
        service.feed.digests = resumed
    deadline = time.monotonic() + timeout if timeout else None
    first = True
    backoff = 1
    while deadline is None or time.monotonic() < deadline:
        replay = ReplaySpool()
        try:
            for name, message in service.feed.reconcile(
                number, resource_id=id, resource_kind=kind or (type if type not in ("all", "unknown") else None)
            ):
                if not predicate(message):
                    continue
                if first and resumed is None:
                    if since:
                        replay.add(message)
                else:
                    stream_output(service, name, message, format)
            if first:
                if resumed is None:
                    records = (
                        replay.records()
                        if since
                        else reversed(
                            [m for m in service.feed.newest(service.feed.max_bodies) if predicate(m)][
                                : tail if tail is not None else int(service.config.settings["cli"]["watch_tail"])
                            ]
                        )
                    )
                    for message in records:
                        stream_output(service, "sms.received", message, format, True)
                diagnostic(
                    "listening",
                    "Listening (complete paginated reconciliation; retention/order guarantees unavailable)",
                    format,
                )
                first = False
            if resume:
                service.state.checkpoint(service.adapter.scope, resume, filters, service.feed.digests)
            backoff = 1
        except (requests.RequestException, TextVerifiedError, TerminalError) as exc:
            if isinstance(exc, TextVerifiedError) and ("HTTP 401" in exc.context or "HTTP 403" in exc.context):
                raise
            if isinstance(exc, TerminalError) and exc.status != 6:
                raise
            if first and resumed is None:
                # A failed initial --since spool has not emitted anything.
                # Rebuild that baseline so already inspected IDs replay too.
                service.feed.digests.clear()
            diagnostic("reconnecting", "Reconnecting; retained server history may have gaps", format, True)
            backoff = max(
                getattr(exc, "retry_after", 0), min(backoff * 2, service.config.settings["sync"]["backoff_max_seconds"])
            )
        finally:
            replay.close()
        delay = backoff if backoff > 1 else service.config.settings["sync"]["sms_interval_seconds"]
        if deadline:
            delay = min(delay, max(0, deadline - time.monotonic()))
        time.sleep(delay)


@sms.command("wait")
def wait(
    ctx: typer.Context,
    number: Optional[str] = None,
    type: str = "all",
    since: Optional[str] = None,
    id: Optional[str] = None,
    kind: Optional[str] = None,
    query: str = "",
    timeout: float = 120,
    code_only: bool = False,
    json_output: bool = typer.Option(False, "--json"),
):
    if timeout < 0 or code_only and json_output:
        raise ValueError("Invalid timeout or incompatible --code-only and --json")
    predicate = sms_filter(number, type, since, id=id, kind=kind, query=query)
    service = workflow(ctx)
    deadline = time.monotonic() + timeout if timeout else None
    first, backoff = True, 1
    while deadline is None or time.monotonic() < deadline:
        candidate = None
        try:
            for name, message in service.feed.reconcile(
                number, resource_id=id, resource_kind=kind or (type if type not in ("all", "unknown") else None)
            ):
                if deadline and time.monotonic() >= deadline:
                    raise TerminalError("No qualifying SMS before timeout", 8, "wait_timeout")
                if (not first or since) and predicate(message) and (not code_only or message["parsed_code"]):
                    if candidate is None or (message["created_at"] or "", message["id"]) < (
                        candidate["created_at"] or "",
                        candidate["id"],
                    ):
                        candidate = message
            if deadline and time.monotonic() >= deadline:
                break
            if candidate is not None:
                if code_only:
                    typer.echo(safe(candidate["parsed_code"]))
                elif json_output:
                    emit(dict(schema_version=1, account=service.adapter.account_scope, message=candidate))
                else:
                    stream_output(service, "sms.received", candidate, "table")
                return
            first, backoff = False, 1
        except (requests.RequestException, TextVerifiedError, TerminalError) as exc:
            if isinstance(exc, TerminalError) and exc.status != 6:
                raise
            if isinstance(exc, TextVerifiedError) and ("HTTP 401" in exc.context or "HTTP 403" in exc.context):
                raise
            if first:
                service.feed.digests.clear()
            diagnostic("reconnecting", "Reconnecting while waiting", "ndjson" if json_output else "table", True)
            backoff = max(
                getattr(exc, "retry_after", 0), min(backoff * 2, service.config.settings["sync"]["backoff_max_seconds"])
            )
        delay = backoff if backoff > 1 else service.config.settings["sync"]["sms_interval_seconds"]
        if deadline:
            delay = min(delay, max(0, deadline - time.monotonic()))
        time.sleep(delay)
    raise TerminalError("No qualifying SMS before timeout", 8, "wait_timeout")


def purchase_command(kind, buy):
    def command(
        ctx: typer.Context,
        service: Optional[str] = None,
        capability: Optional[str] = None,
        duration: Optional[str] = None,
        renewable: Optional[bool] = typer.Option(None, "--renewable/--no-renewable"),
        always_on: Optional[bool] = typer.Option(None, "--always-on/--wakeable"),
        area_code: Optional[List[str]] = typer.Option(None, "--area-code"),
        carrier: Optional[List[str]] = typer.Option(None, "--carrier"),
        max_price: Optional[str] = None,
        require_server_price_cap: bool = False,
        yes: bool = False,
        set_values: Optional[List[str]] = typer.Option(None, "--set"),
        set_json: Optional[List[str]] = typer.Option(None, "--set-json"),
        input_json: Optional[str] = None,
        format: str = "table",
        json_output: bool = typer.Option(False, "--json"),
    ):
        if format not in ("table", "json"):
            raise ValueError("Purchase format must be table or json")
        operation = kind + ".buy"
        sources = []
        if input_json:
            if input_json == "-":
                if buy and not yes:
                    raise ValueError("--input-json - purchases require --yes")
                sources.append(json.load(sys.stdin))
            else:
                sources.append(json.loads(Path(input_json).read_text(encoding="utf-8")))
            if not isinstance(sources[-1], dict):
                raise ValueError("Input JSON must be an object")
        flags = {"service_name": service, "capability": capability, "area_code_select_option": area_code}
        if kind == "rental":
            flags.update(duration=duration, is_renewable=renewable, always_on=always_on)
        else:
            flags.update(carrier_select_option=carrier, max_price=float(max_price) if max_price is not None else None)
        sources.append({k: v for k, v in flags.items() if v is not None})
        sources.extend(scalar(operation, a) for a in set_values or [])
        sources.extend(scalar(operation, a, True) for a in set_json or [])
        inputs = merge_inputs(operation, sources)
        inputs.setdefault("capability", "sms")
        if kind == "rental":
            inputs.setdefault("isRenewable", False)
            inputs.setdefault("numberType", "mobile")
            inputs.setdefault("allowBackOrderReservations", False)
        application = workflow(ctx)
        request, quote = application.quote(kind, inputs, max_price, require_server_price_cap)
        result = dict(request=request.to_api(), quote=quote, account=application.adapter.account_scope)
        if buy:
            approve(
                ctx,
                yes,
                "Buy for account %s? Quote %s (API price unit unspecified); %s; request %s"
                % (
                    application.adapter.username,
                    quote["amount"],
                    quote["price_protection"],
                    json.dumps(request.to_api()),
                ),
            )
            result = application.buy(kind, request, quote)
        if json_output or format == "json":
            emit(dict(schema_version=1, **result))
        else:
            typer.echo(safe(json.dumps(result, indent=2)))

    # Help advertises only inputs supported by this product.
    import inspect

    hidden = {"duration", "renewable", "always_on"} if kind == "verification" else {"carrier"}
    command.__signature__ = inspect.signature(command).replace(
        parameters=[p for name, p in inspect.signature(command).parameters.items() if name not in hidden]
    )
    return command


for group, kind in [(verification, "verification"), (rental, "rental")]:
    group.command("quote")(purchase_command(kind, False))
    group.command("buy")(purchase_command(kind, True))


@verification.command("cancel")
def cancel(ctx: typer.Context, id: str, yes: bool = False):
    approve(ctx, yes, "Cancel verification " + id + "?")
    workflow(ctx).mutate("cancel", id)
    typer.echo("Cancellation accepted")


@rental.command("wake")
def wake(ctx: typer.Context, id: str, yes: bool = False):
    approve(ctx, yes, "Wake rental " + id + "? Cost/window may be assigned by the server.")
    emit(dict(schema_version=1, result=workflow(ctx).mutate("wake", id)))


@schema.command("show")
def schema_show(operation: str):
    emit(descriptor(operation))


@config_app.command("path")
def config_path():
    config = Config()
    emit(
        dict(
            config=str(config.path),
            credentials=str(config.credentials_path),
            state=str(config.state_directory / "state.sqlite3"),
            themes=str(config.directory / "themes"),
        )
    )


@config_app.command("show")
def config_show():
    config = Config()
    emit(dict(schema_version=1, settings=config.settings, profiles=list(config.profiles), source=str(config.path)))


@config_app.command("validate")
def config_validate():
    from .themes import load_theme

    config = Config()
    load_theme(config.settings["appearance"]["theme"], config)
    style = config.settings["appearance"]["style_file"]
    if style:
        from textual.css.stylesheet import Stylesheet

        path = config.directory / style
        sheet = Stylesheet()
        sheet.add_source(path.read_text(encoding="utf-8"))
        sheet.parse()
    typer.echo("Configuration valid")


@theme.command("list")
def theme_list():
    config = Config()
    typer.echo("terminal\ntextverified-dark\ntextverified-light")
    for path in sorted((config.directory / "themes").glob("*.toml")):
        typer.echo("custom:" + path.stem)


@theme.command("set")
def theme_set(name: str):
    from .themes import load_theme

    config = Config()
    load_theme(name, config)
    config.raw.setdefault("appearance", {})["theme"] = name
    config.save()
    typer.echo("Theme: " + name)


def run():
    machine = "--json" in sys.argv or any(value in ("json", "ndjson") for value in sys.argv)
    try:
        app()
    except BrokenPipeError:
        # Avoid a second error during interpreter stdout shutdown.
        sys.stdout = open(os.devnull, "w")
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        if isinstance(exc, TerminalError):
            status, code, message, retryable = exc.status, exc.code, str(exc), exc.retryable
        elif isinstance(exc, (ValueError, TypeError, FileNotFoundError)):
            status, code, message, retryable = 2, "invalid_input", str(exc), False
        elif isinstance(exc, TextVerifiedError):
            if "HTTP 401" in exc.context or "HTTP 403" in exc.context:
                status, code, message, retryable = (
                    3,
                    "authentication_failed",
                    "Authentication failed; check the selected credential pair",
                    False,
                )
            elif "HTTP 404" in exc.context:
                status, code, message, retryable = 4, "not_found", "Requested resource was not found", False
            elif "HTTP 429" in exc.context or "HTTP 5" in exc.context:
                status, code, message, retryable = (
                    6,
                    "read_failed",
                    "API unavailable or rate limited; retry read commands",
                    True,
                )
            else:
                status, code, message, retryable = (
                    5,
                    "api_rejected",
                    "API rejected the request; check balance and inputs",
                    False,
                )
        elif isinstance(exc, requests.RequestException):
            status, code, message, retryable = 6, "network_error", "Network request failed; retry read commands", True
        else:
            status, code, message, retryable = 1, "internal_error", "Internal error (" + type(exc).__name__ + ")", False
        if machine:
            print(
                json.dumps(dict(schema_version=1, error=dict(code=code, message=message, retryable=retryable))),
                file=sys.stderr,
            )
        else:
            print(safe(message), file=sys.stderr)
        return status
    return 0
