"""Keyboard-first Textual shell; SDK calls stay outside the UI loop."""
import asyncio
import datetime as dt
import json
import threading
import re
from pathlib import Path
from rich.text import Text
from textual import on, work
from textual.app import App, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from .adapter import Adapter
from .application import Application
from .config import Config, TerminalError
from .fields import descriptor, merge_inputs
from .models import safe, time_label, matches, state_label, group_label
from .state import State
from .themes import load_theme


def summary_text(values):
    """Readable labels for review and receipt dialogs."""
    lines = []
    for key, value in values.items():
        label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key).replace("_", " ").capitalize()
        if isinstance(value, dict):
            lines.extend([label, summary_text(value), ""])
        else:
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value) or "None"
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            lines.append(label + ": " + safe(value if value is not None else "Unavailable"))
    return "\n".join(lines)


def detail_text(record):
    if "body" in record:
        header = summary_text(
            dict(
                received=record.get("created_at"),
                to=record.get("to_number"),
                sender=record.get("from_number"),
                code=record.get("parsed_code"),
            )
        )
        body = record.get("body")
        return (
            header
            + "\n\n"
            + safe(body if body is not None else "Message " + record.get("content_state", "unavailable"))
        )
    return summary_text(
        dict(
            number=record.get("number"),
            service=record.get("service"),
            type=group_label(record),
            status=state_label(record),
            created=record.get("created_at"),
            expires=record.get("expires_at"),
            renews=record.get("renews_at"),
            actions=record.get("available_actions", []),
        )
    )


class Notice(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, title, content):
        super().__init__()
        self.heading, self.content = title, content

    def compose(self):
        with Vertical(classes="dialog"):
            yield Label(self.heading, markup=False)
            yield TextArea(safe(self.content), read_only=True, id="notice-text")
            yield Button("Close", id="close")

    @on(Button.Pressed, "#close")
    def close(self):
        self.dismiss()


class Confirm(ModalScreen):
    BINDINGS = [("escape", "back", "Back")]

    def __init__(self, content, callback, label="Confirm purchase"):
        super().__init__()
        self.content, self.callback, self.label = content, callback, label
        self.submitted = False

    def compose(self):
        with Vertical(classes="dialog", id="purchase-review"):
            yield TextArea(safe(self.content), read_only=True, id="review-text")
            with Horizontal(classes="buttons"):
                yield Button("Back", id="back")
                yield Button(self.label, id="confirm", variant="warning")

    def on_mount(self):
        self.query_one("#back", Button).focus()

    def action_back(self):
        if not self.submitted:
            self.dismiss()

    @on(Button.Pressed)
    def pressed(self, event):
        if event.button.id == "back":
            self.action_back()
        elif event.button.id == "confirm" and not self.submitted:
            self.submitted = True
            event.button.disabled = True
            self.query_one("#back", Button).disabled = True
            self.app.run_worker(self.submit(), exit_on_error=False)

    async def submit(self):
        try:
            result = await self.callback()
            self.dismiss()
            self.app.push_screen(Notice("Operation receipt", summary_text(result)))
            self.app.last_resources = self.app.last_account = 0
            self.app.action_refresh()
        except Exception as exc:
            self.dismiss()
            self.app.push_screen(Notice("Operation result", self.app.error_text(exc)))


class Purchase(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Cancel")]

    def __init__(self, kind):
        super().__init__()
        self.kind, self.revision, self.busy = kind, 0, False

    def compose(self):
        with VerticalScroll(classes="dialog", id="purchase-modal"):
            yield Label("Buy " + self.kind, markup=False)
            yield Label("Service (type to search fetched catalog)")
            yield Input(placeholder="Service name", id="service")
            capability = next(
                f["schema"].get("enum", [])
                for f in descriptor(self.kind + ".buy")["fields"]
                if f["api_field_name"] == "capability"
            )
            yield Select([(v, v) for v in capability], value="sms", allow_blank=False, id="capability")
            if self.kind == "rental":
                durations = next(
                    f["schema"]["enum"] for f in descriptor("rental.buy")["fields"] if f["api_field_name"] == "duration"
                )
                yield Select([(v, v) for v in durations], prompt="Choose duration", id="duration")
                yield Checkbox("Renewable (recurring commitment)", id="renewable")
                yield Label("Receiving: always-on per pinned API schema")
            yield Input(placeholder="Maximum price (optional)", id="max-price", type="number")
            yield Label("Advanced: JSON object. All writable fields supported; do not duplicate common fields.")
            yield TextArea("{}", id="advanced")
            yield Static("Quote required before purchase", id="quote-status", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Cancel", id="cancel-purchase")
                yield Button("Get quote / Review", id="quote")
                yield Button("Fields", id="fields")

    def on_mount(self):
        self.query_one("#service", Input).focus()
        self.load_services()

    @work(exclusive=True, exit_on_error=False)
    async def load_services(self):
        try:
            names = await asyncio.to_thread(self.app.application.adapter.services, self.kind)
            self.query_one("#service", Input).suggester = SuggestFromList(names, case_sensitive=False)
        except Exception:
            self.query_one("#quote-status", Static).update("Catalog unavailable; enter a known service, then quote")

    @on(Input.Changed)
    @on(Select.Changed)
    @on(Checkbox.Changed)
    @on(TextArea.Changed)
    def invalidate(self):
        self.revision += 1

    @on(Button.Pressed)
    def pressed(self, event):
        if event.button.id == "cancel-purchase":
            self.dismiss()
        elif event.button.id == "fields":
            fields = descriptor(self.kind + ".buy")["fields"]
            content = "\n\n".join(
                field["api_field_name"]
                + (" (required)" if field["required"] else " (optional)")
                + "\n"
                + field["schema"].get("description", field["schema"].get("type", ""))
                + (
                    "\nChoices: " + ", ".join(str(value) for value in field["schema"]["enum"])
                    if "enum" in field["schema"]
                    else ""
                )
                for field in fields
            )
            self.app.push_screen(Notice("Request fields", content))
        elif event.button.id == "quote" and not self.busy:
            self.quote()

    @work(exclusive=True, exit_on_error=False)
    async def quote(self):
        self.busy = True
        self.query_one("#quote", Button).disabled = True
        revision = self.revision
        try:
            common = dict(
                serviceName=self.query_one("#service", Input).value,
                capability=self.query_one("#capability", Select).value,
            )
            if self.kind == "rental":
                duration = self.query_one("#duration", Select).value
                if duration is Select.BLANK:
                    raise ValueError("Choose a rental duration")
                common.update(duration=duration, isRenewable=self.query_one("#renewable", Checkbox).value)
            maximum = self.query_one("#max-price", Input).value or None
            if maximum and self.kind == "verification":
                common["maxPrice"] = float(maximum)
            advanced = json.loads(self.query_one("#advanced", TextArea).text)
            if not isinstance(advanced, dict):
                raise ValueError("Advanced input must be a JSON object")
            inputs = merge_inputs(self.kind + ".buy", [common, advanced])
            if self.kind == "rental":
                inputs.setdefault("numberType", "mobile")
                inputs.setdefault("allowBackOrderReservations", False)
            service = self.app.application
            request, quote = await asyncio.to_thread(service.quote, self.kind, inputs, maximum)
            account = await asyncio.to_thread(service.adapter.account)
            if revision != self.revision:
                self.query_one("#quote-status", Static).update("Inputs changed; quote discarded. Quote again.")
                return
            summary = dict(
                account=account,
                request=request.to_api(),
                quote=quote,
                warning="Quote is not an inventory reservation. Rental limits are preflight only. Renewable rentals recur.",
            )

            async def buy():
                if revision != self.revision:
                    raise ValueError("Inputs changed; obtain a new quote")
                result = await asyncio.to_thread(service.buy, self.kind, request, quote)
                return result

            self.app.push_screen(Confirm(summary_text(summary), buy))
        except Exception as exc:
            self.query_one("#quote-status", Static).update(self.app.error_text(exc))
        finally:
            self.busy = False
            self.query_one("#quote", Button).disabled = False


class Login(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Back")]

    def compose(self):
        with VerticalScroll(classes="dialog", id="login-dialog"):
            yield Label("TextVerified", classes="dialog-title")
            yield Static("Sign in to manage your numbers and messages", classes="dialog-subtitle")
            yield Label("Email")
            yield Input(placeholder="you@example.com", id="login-user")
            yield Label("API key")
            yield Input(placeholder="API key", password=True, id="login-key")
            yield Static("Saved automatically to your local credential cache.", id="login-status", markup=False)
            with Horizontal(classes="buttons"):
                yield Button("Back", id="login-back")
                yield Button("Sign in", id="login-submit", variant="primary")

    def on_mount(self):
        self.query_one("#login-user", Input).focus()

    @on(Input.Submitted)
    def submitted(self, event):
        if event.input.id == "login-user":
            self.query_one("#login-key", Input).focus()
        elif not self.query_one("#login-submit", Button).disabled:
            self.login()

    @on(Button.Pressed)
    def pressed(self, event):
        if event.button.id == "login-back":
            self.dismiss()
        else:
            self.login()

    @work(exclusive=True, exit_on_error=False)
    async def login(self):
        button = self.query_one("#login-submit", Button)
        button.disabled = True
        adapter = None
        try:
            user = self.query_one("#login-user", Input).value.strip()
            key = self.query_one("#login-key", Input).value
            profile = self.app.profile or "default"
            if not user or not key:
                raise ValueError("Email and API key are required")
            adapter = Adapter(user, key, profile, self.app.config.settings["sync"]["request_timeout_seconds"])
            account = await asyncio.to_thread(adapter.account)
            await asyncio.to_thread(self.app.config.save_credentials, user, key, profile)
            self.app.switch_application(Application(adapter, self.app.config, State(self.app.config)), account=account)
            self.dismiss()
        except Exception as exc:
            if adapter:
                adapter.close()
            self.query_one("#login-status", Static).update(self.app.error_text(exc))
        finally:
            button.disabled = False


class Profiles(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close")]

    def compose(self):
        with Vertical(classes="dialog"):
            yield Label("Switch account")
            yield Select(
                [("Environment credentials", "")] + [(name, name) for name in self.app.config.profiles],
                id="profile-select",
            )
            with Horizontal(classes="buttons"):
                yield Button("Switch", id="profile-switch")
                yield Button("Login", id="profile-login")
                yield Button("Close", id="profile-close")
            yield Static("", id="profile-status", markup=False)

    @on(Button.Pressed)
    def pressed(self, event):
        if event.button.id == "profile-close":
            self.dismiss()
        elif event.button.id == "profile-login":
            self.dismiss()
            self.app.push_screen(Login())
        else:
            self.switch()

    @work(exclusive=True, exit_on_error=False)
    async def switch(self):
        try:
            name = self.query_one("#profile-select", Select).value
            if name is Select.BLANK:
                raise ValueError("Select a profile")
            user, key, profile = self.app.config.credentials(name or None)
            adapter = Adapter(user, key, profile)
            account = await asyncio.to_thread(adapter.account)
            self.app.switch_application(Application(adapter, self.app.config, State(self.app.config)), account=account)
            self.dismiss()
        except Exception as exc:
            self.query_one("#profile-status", Static).update(self.app.error_text(exc))


class NumbersTable(DataTable):
    def action_cursor_up(self):
        if self.cursor_row == 0:
            self.app.query_one("#buy-verification", Button).focus()
        else:
            super().action_cursor_up()


class TerminalApp(App):
    TITLE = "TextVerified"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        Binding("1", "numbers", "Numbers"),
        Binding("2", "inbox", "Inbox"),
        Binding("v", "verify", "Verify"),
        Binding("r", "rent", "Rent"),
        Binding("/", "search", "Search"),
        Binding("f", "filters", "Filters", show=False),
        Binding("a", "actions", "Actions"),
        Binding("c", "copy_code", "Code"),
        Binding("n", "copy_number", "Number", show=False),
        Binding("y", "copy_body", "Message", show=False),
        Binding("g", "newest", "Newest", show=False),
        Binding("f5", "force_refresh", "Refresh"),
        Binding("?", "help", "Help"),
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("escape", "close_detail", "Back", show=False),
    ]

    def __init__(self, application=None, config=None, profile=None, selected_theme=None, reset_style=False):
        super().__init__()
        self.application, self.config, self.profile = application, config or Config(), profile
        self.numbers, self.messages, self.errors = {}, {}, {}
        self._rendering = False
        self.account = None
        self.selected_resource = self.selected_message = None
        self.following, self.unread, self.new_count = True, set(), 0
        self.context_generation, self.refreshing = 0, False
        self.retry_until, self.retry_delay = 0, 1
        self.scan_cancel = threading.Event()
        self.last_resources = self.last_account = self.last_details = 0
        self.history_results, self.retired = {}, []
        self.style_error = None
        for name in ("terminal", "textverified-dark", "textverified-light"):
            self.register_theme(load_theme(name, self.config))
        name = "terminal" if reset_style else selected_theme or self.config.settings["appearance"]["theme"]
        try:
            self.register_theme(load_theme(name, self.config))
            self.theme = name
        except (ValueError, OSError) as exc:
            self.theme, self.style_error = "terminal", str(exc)
        if __import__("os").environ.get("NO_COLOR") or self.config.settings["appearance"]["color"] == "never":
            self.console.no_color = True
        style = self.config.settings["appearance"]["style_file"]
        if style and not reset_style:
            try:
                from textual.css.stylesheet import Stylesheet

                path = self.config.directory / style
                sheet = Stylesheet()
                sheet.add_source(path.read_text(encoding="utf-8"))
                sheet.parse()
                self.CSS_PATH = [Path(__file__).with_name("app.tcss"), path]
            except Exception:
                self.style_error = "Invalid TCSS; bundled stylesheet loaded. Use tui --reset-style."

    def compose(self):
        yield Static("TextVerified | Connecting", id="account-bar", markup=False)
        yield Static("", id="small-terminal", markup=False)
        with TabbedContent(initial=self.config.settings["ui"]["initial_view"], id="views"):
            with TabPane("1 Numbers", id="numbers"):
                with Horizontal(id="purchase-strip"):
                    yield Button("Buy verification", id="buy-verification", variant="primary")
                    yield Button("Buy rental", id="buy-rental")
                with Horizontal(classes="search-strip"):
                    yield Input(placeholder="Search loaded resources", id="numbers-search")
                    yield Select(
                        [("Loaded", "loaded"), ("All API history", "history")],
                        value="loaded",
                        allow_blank=False,
                        id="numbers-scope",
                    )
                    yield Select(
                        [(v.title(), v) for v in ("all", "active", "history", "attention")],
                        value="all",
                        allow_blank=False,
                        id="numbers-filter",
                    )
                yield NumbersTable(id="numbers-list", cursor_type="row", zebra_stripes=True)
            with TabPane("2 Inbox", id="inbox"):
                with Horizontal(classes="search-strip"):
                    yield Input(placeholder="Search loaded messages", id="inbox-search")
                    yield Select(
                        [("Loaded", "loaded"), ("All API history", "history")],
                        value="loaded",
                        allow_blank=False,
                        id="inbox-scope",
                    )
                yield DataTable(id="inbox-list", cursor_type="row", zebra_stripes=True)
        yield Static("Loaded scope; API retention applies", id="coverage", markup=False)
        yield TextArea("Select a row and press Enter for complete details", read_only=True, id="details")
        with Horizontal(id="controls"):
            yield Footer()
            yield Static("", id="clock", markup=False)

    def on_mount(self):
        self.query_one("#details", TextArea).display = False
        self.query_one("#numbers-list", DataTable).add_columns(
            "Kind / service", "Number", "State / readiness", "Time", "Latest SMS"
        )
        inbox = self.query_one("#inbox-list", DataTable)
        for label, width in (
            ("Time", 16),
            ("To", 15),
            ("From", 12),
            ("Code", 10),
            ("Body", max(24, self.size.width - 65)),
        ):
            inbox.add_column(label, width=width)
        self.query_one("#numbers-list", DataTable).focus()
        self.set_interval(1, self.paint_time)
        self.set_interval(self.config.settings["sync"]["sms_interval_seconds"], self.action_refresh)
        if self.style_error:
            self.notify(safe(self.style_error), severity="warning")
        if self.application is None:
            self.query_one("#account-bar", Static).update("TextVerified | Authentication required")
            self.push_screen(Login())
        else:
            if not self.application.state.durable:
                self.notify("State storage unavailable; session-only read markers", severity="warning")
            self.action_refresh()

    def check_action(self, action, parameters):
        if (
            action in {"copy_code", "copy_body", "newest"}
            and self.is_mounted
            and self.query_one("#views", TabbedContent).active != "inbox"
        ):
            return False
        if isinstance(self.screen, ModalScreen) and action in {
            "numbers",
            "inbox",
            "verify",
            "rent",
            "search",
            "filters",
            "actions",
            "copy_code",
            "copy_number",
            "copy_body",
            "newest",
            "help",
            "quit",
        }:
            return False
        if (
            action
            in {
                "numbers",
                "inbox",
                "verify",
                "rent",
                "search",
                "filters",
                "actions",
                "copy_code",
                "copy_number",
                "copy_body",
                "newest",
                "help",
                "quit",
            }
            and isinstance(self.focused, (Input, TextArea))
            and not (isinstance(self.focused, TextArea) and self.focused.read_only)
        ):
            return False
        return True

    def error_text(self, error):
        if isinstance(error, (TerminalError, ValueError)):
            return safe(str(error))
        return "Request failed (" + type(error).__name__ + "); check credentials/network. Last known data retained."

    def switch_application(self, application, account=None):
        if self.application:
            self.application.cancelled.set()
            self.retired.append(self.application)
        self.scan_cancel.set()
        self.context_generation += 1
        self.retry_until, self.retry_delay = 0, 1
        self.application = application
        self.numbers.clear()
        self.messages.clear()
        self.unread.clear()
        self.history_results.clear()
        self.selected_resource = self.selected_message = None
        self.account = account
        self.errors.clear()
        self.last_resources = self.last_account = self.last_details = 0
        if account is not None:
            import time

            self.last_account = time.monotonic()
        self.paint_header()
        self.render_rows()
        self.refreshing = False
        self.action_refresh()

    def action_force_refresh(self):
        self.last_resources = self.last_account = self.last_details = 0
        self.action_refresh()

    def action_refresh(self):
        import time

        if self.application and not self.refreshing and time.monotonic() >= self.retry_until:
            self.refreshing = True
            self.refresh_data()

    @work(exit_on_error=False)
    async def refresh_data(self):
        import time

        service, generation = self.application, self.context_generation
        baseline = service.feed.baseline
        try:
            try:
                iterator = iter(service.feed.reconcile(cancel=service.cancelled))

                def batch():
                    from itertools import islice

                    return list(islice(iterator, 100))

                while True:
                    incoming = await asyncio.to_thread(batch)
                    if generation != self.context_generation:
                        return
                    self.messages = dict(service.feed.messages)
                    if self.config.settings["storage"]["persist_read_markers"]:
                        self.unread.update(
                            service.state.observe(
                                service.adapter.scope, [m for _, m in incoming], baseline=not baseline
                            )
                        )
                    if baseline:
                        for name, message in incoming:
                            if name == "sms.received" and not service.state.read(service.adapter.scope, message["id"]):
                                self.unread.add(message["id"])
                                if not self.following:
                                    self.new_count += 1
                    if not incoming:
                        break
                    self.render_rows()
                    await asyncio.sleep(0)
                self.errors.pop("sms", None)
                self.retry_delay = 1
                warnings = getattr(service.adapter, "warnings", [])
                if warnings:
                    self.errors["coverage"] = "; ".join(warnings)
                if self.selected_message and self.selected_message in self.messages:
                    self.query_one("#details", TextArea).load_text(detail_text(self.messages[self.selected_message]))
            except Exception as exc:
                if generation != self.context_generation:
                    return
                self.errors["sms"] = self.error_text(exc)
                self.retry_delay = min(self.retry_delay * 2, self.config.settings["sync"]["backoff_max_seconds"])
                self.retry_until = time.monotonic() + max(self.retry_delay, getattr(exc, "retry_after", 0))
            if time.monotonic() - self.last_resources >= self.config.settings["sync"]["resources_interval_seconds"]:
                try:
                    rows = await asyncio.to_thread(service.numbers)
                    if generation != self.context_generation:
                        return
                    self.numbers = {row["key"]: row for row in rows}
                    self.last_resources = time.monotonic()
                    self.errors.pop("numbers", None)
                except Exception as exc:
                    self.errors["numbers"] = self.error_text(exc)
            if time.monotonic() - self.last_details >= self.config.settings["sync"]["verification_interval_seconds"]:
                for row in list(self.numbers.values()):
                    if row["kind"] == "verification" and row["lifecycle"] == "active":
                        try:
                            detail = await asyncio.to_thread(service.adapter.details, row["kind"], row["resource_id"])
                            if generation != self.context_generation:
                                return
                            self.numbers[row["key"]] = detail
                        except Exception as exc:
                            self.errors["verification"] = self.error_text(exc)
                self.last_details = time.monotonic()
            if time.monotonic() - self.last_account >= self.config.settings["sync"]["account_interval_seconds"]:
                try:
                    account = await asyncio.to_thread(service.adapter.account)
                    if generation != self.context_generation:
                        return
                    self.account = account
                    self.last_account = time.monotonic()
                    self.errors.pop("account", None)
                except Exception as exc:
                    self.errors["account"] = self.error_text(exc)
            if generation == self.context_generation:
                self.render_rows()
                self.paint_header()
        finally:
            if generation == self.context_generation:
                self.refreshing = False

    def paint_header(self):
        account = self.account or {}
        label = account.get("username") or (self.application.adapter.username if self.application else "Unknown")
        balance = account.get("balance_amount", "Unknown")
        status = "Offline / stale" if self.errors else "Connected" if self.account else "Connecting"
        self.query_one("#account-bar", Static).update(
            safe(
                "TextVerified | "
                + label
                + " | Balance: "
                + balance
                + " credits"
                + (" stale" if "account" in self.errors else "")
                + " | "
                + status
            )
        )

    def paint_time(self):
        zone = self.config.settings["ui"]["timezone"]
        if zone == "local":
            local = dt.datetime.now().astimezone()
        else:
            from zoneinfo import ZoneInfo

            local = dt.datetime.now(ZoneInfo(zone))
        self.query_one("#clock", Static).display = self.size.width >= 80 and self.config.settings["ui"]["show_clock"]
        self.query_one("#clock", Static).update(
            local.strftime("%H:%M:%S" if self.config.settings["ui"]["clock_seconds"] else "%H:%M")
        )
        table = self.query_one("#numbers-list", DataTable)
        for row in self.numbers.values():
            if row["kind"] == "verification":
                try:
                    table.update_cell(row["key"], table.ordered_columns[3].key, time_label(row))
                except Exception:
                    pass
        small = self.size.width < 60 or self.size.height < 16
        self.query_one("#small-terminal", Static).update(
            "Terminal too small: resize to 60 x 16 or use the CLI" if small else ""
        )
        self.query_one("#small-terminal", Static).display = small
        self.query_one("#views", TabbedContent).display = not small
        self.query_one("#details", TextArea).display = (
            not small and self.size.height >= 24 and bool(self.selected_resource or self.selected_message)
        )
        self.query_one("#coverage", Static).display = not small

    def render_rows(self):
        self._rendering = True
        from .models import sort_number

        for name, rows in [("numbers", self.numbers), ("inbox", self.messages)]:
            table = self.query_one("#" + name + "-list", DataTable)
            selected = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value if table.row_count else None
            old_scroll = table.scroll_y
            query = self.query_one("#" + name + "-search", Input).value
            scope = self.query_one("#" + name + "-scope", Select).value
            values = (
                self.history_results.get(name, {}).values()
                if scope == "history" and name in self.history_results
                else rows.values()
            )
            values = [row for row in values if matches(row, query)]
            table.clear()
            if name == "numbers":
                state = self.query_one("#numbers-filter", Select).value
                values = sorted((r for r in values if state == "all" or r["lifecycle"] == state), key=sort_number)
                latest_by_number = {}
                for message in sorted(self.messages.values(), key=lambda m: m["created_at"] or "", reverse=True):
                    latest_by_number.setdefault(message["to_number"], message)
                for row in values:
                    latest = latest_by_number.get(row["number"])
                    preview = (
                        (latest["parsed_code"] or latest["body"] or latest["content_state"]) + " (number match)"
                        if latest
                        else "No SMS loaded"
                    )
                    table.add_row(
                        Text(safe(group_label(row) + " / " + str(row["service"] or "Unknown"))),
                        Text(safe(row["number"])),
                        Text(safe(state_label(row))),
                        time_label(row),
                        Text(safe(preview).replace("\n", " ")),
                        key=row["key"],
                    )
                key_name = "key"
            else:
                values.sort(key=lambda m: (m["created_at"] or "", m["id"]), reverse=True)
                for row in values:
                    table.add_row(
                        Text(safe(row["created_at"]).replace("T", " ")[:16]),
                        Text(safe(row["to_number"])),
                        Text(safe(row["from_number"])),
                        Text(safe(("* " if row["id"] in self.unread else "") + (row["parsed_code"] or ""))),
                        Text(safe(row["body"] if row["body"] is not None else row["content_state"]).replace("\n", " ")),
                        key=row["id"],
                    )
                key_name = "id"
            keys = [r[key_name] for r in values]
            if name == "inbox" and self.following:
                table.move_cursor(row=0, animate=False)
            elif selected in keys:
                table.move_cursor(row=keys.index(selected), animate=False, scroll=False)
                table.scroll_to(y=old_scroll, animate=False)
        self.query_one("#coverage", Static).update(
            "Loaded scope | %d retained messages | %d new | %s"
            % (
                len(self.messages),
                self.new_count,
                "Incomplete / stale: " + "; ".join(self.errors)
                if self.errors
                else "API history; retention/order unknown",
            )
        )

        self._rendering = False

    @on(Input.Changed)
    def search_changed(self, event):
        if event.input.id in ("numbers-search", "inbox-search"):
            self.render_rows()

    @on(Select.Changed)
    def scope_changed(self, event):
        if event.select.id in ("numbers-scope", "inbox-scope") and event.value == "history":
            self.history_scan(event.select.id.split("-")[0])
        elif event.select.id in ("numbers-scope", "inbox-scope", "numbers-filter"):
            self.render_rows()

    @work(group="history", exclusive=True, exit_on_error=False)
    async def history_scan(self, view):
        self.scan_cancel.set()
        self.scan_cancel = threading.Event()
        cancelled = self.scan_cancel
        service, generation = self.application, self.context_generation
        if not service:
            return
        self.history_results[view] = {}
        query = self.query_one("#" + view + "-search", Input).value
        count = 0
        try:
            iterator = iter(
                service.adapter.messages(cancel=cancelled)
                if view == "inbox"
                else service.adapter.resources(cancel=cancelled)
            )

            def batch():
                from itertools import islice

                return list(islice(iterator, 100))

            while not cancelled.is_set():
                rows = await asyncio.to_thread(batch)
                if generation != self.context_generation:
                    return
                if not rows:
                    break
                for row in rows:
                    count += 1
                    if matches(row, query):
                        self.history_results[view][row.get("key", row.get("id"))] = row
                        if len(self.history_results[view]) > service.feed.max_bodies:
                            self.history_results[view].pop(next(iter(self.history_results[view])))
                self.render_rows()
                self.query_one("#coverage", Static).update(
                    "Searching API history: %d scanned; %d matches retained (bounded window)"
                    % (count, len(self.history_results[view]))
                )
                await asyncio.sleep(0)
            self.query_one("#coverage", Static).update(
                "API history %s: %d scanned; bounded result window; retention applies"
                % ("cancelled / incomplete" if cancelled.is_set() else "complete", count)
            )
        except Exception as exc:
            self.query_one("#coverage", Static).update(
                "API history incomplete: %d scanned; %s" % (count, self.error_text(exc))
            )

    @on(DataTable.RowHighlighted, "#inbox-list")
    def highlighted(self, event):
        if event.cursor_row > 0 and not self._rendering:
            self.following = False

    @on(DataTable.RowSelected)
    def row_opened(self, event):
        identity = event.row_key.value
        if event.data_table.id == "inbox-list":
            self.selected_message = identity
            self.application.feed.pinned = {identity}
            self.following = False
            message = self.messages.get(identity) or self.history_results.get("inbox", {}).get(identity)
            if message:
                self.unread.discard(identity)
                if self.config.settings["storage"]["persist_read_markers"]:
                    self.application.state.mark_read(self.application.adapter.scope, identity)
                self.show_details(message)
        else:
            self.selected_resource = identity
            row = self.numbers.get(identity) or self.history_results.get("numbers", {}).get(identity)
            if row:
                self.show_details(row)
                self.load_details(row)

    def show_details(self, record):
        content = detail_text(record)
        self.query_one("#details", TextArea).load_text(content)
        if self.size.height < 24:
            self.push_screen(Notice("Details", content))
        else:
            self.query_one("#details", TextArea).display = True

    @work(group="details", exclusive=True, exit_on_error=False)
    async def load_details(self, row):
        service, generation = self.application, self.context_generation
        try:
            value = await asyncio.to_thread(service.adapter.details, row["kind"], row["resource_id"])
            if generation == self.context_generation and self.selected_resource == row["key"]:
                self.numbers[row["key"]] = value
                self.query_one("#details", TextArea).load_text(detail_text(value))
        except Exception as exc:
            self.notify(self.error_text(exc), severity="warning")

    @on(Button.Pressed)
    def button_pressed(self, event):
        if event.button.id == "buy-verification":
            self.action_verify()
        elif event.button.id == "buy-rental":
            self.action_rent()

    def on_click(self, event):
        if event.widget and event.widget.id == "account-bar":
            self.action_account()

    def action_quit(self):
        if self.application and self.application.mutation_lock.locked():
            self.notify("Waiting for submitted operation to finish and write its receipt", severity="warning")
            return
        self.scan_cancel.set()
        if self.application:
            self.application.cancelled.set()
        self.exit()

    def action_account(self):
        self.push_screen(
            Notice(
                "Account and connection",
                summary_text(
                    dict(
                        email=(self.account or {}).get("username"),
                        balance=(self.account or {}).get("balance_amount"),
                        connection="Offline / stale" if self.errors else "Connected" if self.account else "Connecting",
                        **({"sync_issues": self.errors} if self.errors else {}),
                    )
                ),
            )
        )

    def action_profiles(self):
        self.push_screen(Profiles())

    def action_numbers(self):
        self.query_one("#views", TabbedContent).active = "numbers"
        self.query_one("#numbers-list", DataTable).focus()

    def action_inbox(self):
        self.query_one("#views", TabbedContent).active = "inbox"
        self.query_one("#inbox-list", DataTable).focus()

    def action_verify(self):
        self.push_screen(Purchase("verification") if self.application else Login())

    def action_rent(self):
        self.push_screen(Purchase("rental") if self.application else Login())

    def action_search(self):
        view = self.query_one("#views", TabbedContent).active
        self.query_one("#" + view + "-search", Input).focus()

    def action_filters(self):
        view = self.query_one("#views", TabbedContent).active
        self.query_one("#" + view + "-scope", Select).focus()

    def action_newest(self):
        self.following = True
        self.new_count = 0
        if self.application:
            self.application.feed.pinned.clear()
        self.query_one("#inbox-list", DataTable).move_cursor(row=0, animate=False)

    def action_close_detail(self):
        self.scan_cancel.set()
        self.selected_resource = self.selected_message = None
        self.query_one("#details", TextArea).load_text("Select a row and press Enter for complete details")
        view = self.query_one("#views", TabbedContent).active
        self.query_one("#" + view + "-list", DataTable).focus()

    def selected(self):
        view = self.query_one("#views", TabbedContent).active
        table = self.query_one("#" + view + "-list", DataTable)
        if table.row_count:
            identity = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
            rows = self.messages if view == "inbox" else self.numbers
            return rows.get(identity) or self.history_results.get(view, {}).get(identity)
        return None

    def copy_value(self, field):
        value = (self.selected() or {}).get(field)
        if not value:
            self.notify("Value unavailable; open details for selectable text", severity="warning")
            return
        self.copy_to_clipboard(safe(value))
        self.notify("Clipboard request sent; terminal acceptance cannot be verified. Details provide selectable text.")

    def action_copy_code(self):
        self.copy_value("parsed_code")

    def action_copy_number(self):
        self.copy_value("to_number" if self.query_one("#views", TabbedContent).active == "inbox" else "number")

    def action_copy_body(self):
        self.copy_value("body")

    def action_actions(self):
        row = self.selected()
        if not row or not row.get("available_actions"):
            self.notify("No supported actions; open resource details first")
            return
        action, identity, service = row["available_actions"][0], row["resource_id"], self.application

        async def mutate():
            return await asyncio.to_thread(service.mutate, action, identity)

        self.push_screen(
            Confirm(
                "%s resource %s for account %s? Server determines eligibility and any cost."
                % (action.title(), identity, service.adapter.username),
                mutate,
                "Confirm " + action,
            )
        )

    def action_help(self):
        self.push_screen(
            Notice(
                "Keyboard help",
                "1 Numbers | 2 Inbox | Tab/Shift+Tab focus | Up/Down select | Enter details\n/ Search | f Scope | v Buy verification | r Buy rental | a Actions\nc Copy code | n Copy number | y Copy message | g Newest\nF5 Refresh | Ctrl+P Palette (account/profile/theme) | Esc Back | q Quit\nSingle-character shortcuts do not fire in editable fields.\nInbox is account-wide; read views never wake or purchase.\nHistory search has a bounded result window; CLI --all exports full available history.",
            )
        )

    def action_reset_theme(self):
        self.theme = "terminal"
        self.config.raw.setdefault("appearance", {})["theme"] = "terminal"
        self.config.save()

    def get_system_commands(self, screen):
        yield from super().get_system_commands(screen)
        yield SystemCommand("Account details", "Identity, balance, freshness and subsystem errors", self.action_account)
        yield SystemCommand("Switch profile", "Switch whole account context", self.action_profiles)
        yield SystemCommand("Buy verification", "Quote and review first", self.action_verify)
        yield SystemCommand("Buy rental", "Quote and review first", self.action_rent)
        yield SystemCommand("Reset to terminal theme", "Restore terminal palette", self.action_reset_theme)
        from functools import partial

        names = ["terminal", "textverified-dark", "textverified-light"] + [
            "custom:" + p.stem for p in (self.config.directory / "themes").glob("*.toml")
        ]
        for name in names:
            yield SystemCommand("Theme: " + name, "Preview and save theme", partial(self.apply_theme, name))

    def apply_theme(self, name):
        try:
            self.register_theme(load_theme(name, self.config))
            self.theme = name
            self.config.raw.setdefault("appearance", {})["theme"] = name
            self.config.save()
        except (ValueError, OSError) as exc:
            self.notify(safe(str(exc)), severity="warning")

    def on_unmount(self):
        self.scan_cancel.set()
        if self.application:
            self.application.cancelled.set()
        for service in self.retired:
            service.cancelled.set()

    def run(self, *args, **kwargs):
        try:
            return super().run(*args, **kwargs)
        finally:
            # App.run waits for its loop/executor shutdown before closing SDK
            # sessions, including accounts created by the interactive login.
            if self.application:
                self.application.close()
            for service in self.retired:
                service.close()
