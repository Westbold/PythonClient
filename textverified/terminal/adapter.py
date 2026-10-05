"""SDK boundary. Widgets and commands do not own endpoint URLs."""
import threading
from decimal import Decimal
from urllib.parse import quote, urlparse
from textverified.action import _Action
from textverified import TextVerified, __version__
from textverified.data import NewVerificationRequest, NewRentalRequest, NumberType, ReservationType
from .models import number_record, message_record, now


def _read_link(client, data):
    """Validate a server-supplied read link before following it."""
    from urllib.parse import urljoin, urlparse

    action = data if isinstance(data, _Action) else _Action.from_api(data)
    origin = getattr(client, "base_url", None)
    if action.method.upper() != "GET":
        raise ValueError("Follow-up links must use GET")
    if origin:
        source, target = urlparse(origin), urlparse(urljoin(origin, action.href))
        if (source.scheme, source.netloc) != (target.scheme, target.netloc):
            raise ValueError("Cross-origin follow-up link")
    return action


def _iter_api_pages(api_context, action, **kwargs):
    """Stream terminal history through the existing SDK transport."""
    seen = set()
    while True:
        action = _read_link(api_context, action)
        if action.href in seen:
            raise ValueError("Cyclic pagination link")
        seen.add(action.href)
        page = api_context._perform_action(action, **kwargs).data
        kwargs = {}
        if not isinstance(page, dict) or not isinstance(page.get("data"), list):
            raise ValueError("Invalid paginated response")
        yield page
        if not page.get("hasNext", False):
            return
        link = page.get("links", {}).get("next")
        if not link:
            raise ValueError("Missing next link on incomplete page")
        action = _Action.from_api(link)


class Adapter:
    def __init__(self, username, key, profile=None, timeout=15):
        self.client = TextVerified(
            api_username=username, api_key=key, user_agent=f"TextVerified-Python-TUI/{__version__}"
        )
        # urllib3 connection retries also apply to POSTs; disable them here.
        # Application reconnection repeats reads only, never mutations.
        from requests.adapters import HTTPAdapter

        self.client.session.mount("https://", HTTPAdapter(max_retries=0))
        self.client.session.mount("http://", HTTPAdapter(max_retries=0))
        # Bound auth, pagination and detail requests without changing SDK defaults.
        original = self.client.session.request

        def request(*args, **kwargs):
            kwargs.setdefault("timeout", timeout)
            # Safe GETs have a finite retry budget; POSTs are dispatched once.
            import time
            import random
            import requests

            method = kwargs.get("method", args[0] if args else "GET").upper()
            for attempt in range(3 if method == "GET" else 1):
                try:
                    response = original(*args, **kwargs)
                except requests.RequestException:
                    if method != "GET" or attempt == 2:
                        raise
                    time.sleep(2**attempt + random.random() / 4)
                    continue
                if method != "GET" or response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                    return response
                delay = 2**attempt + random.random() / 4
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        from email.utils import parsedate_to_datetime
                        from datetime import datetime, timezone

                        delay = max(
                            0, (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
                        )
                if delay > timeout:
                    # Let the session scheduler honor a long server delay.
                    from .config import TerminalError

                    error = TerminalError("Rate limited; next read must wait", 6, "rate_limited", True)
                    error.retry_after = delay
                    raise error
                response.close()
                time.sleep(delay)

        self.client.session.request = request
        self.profile = profile
        self.username = username
        self.lock = threading.RLock()
        self.warnings = []
        self.scope = self.client.base_url + "|" + username

    @property
    def account_scope(self):
        return dict(profile=self.profile, username=self.username, api_origin=self.client.base_url)

    def account(self):
        with self.lock:
            account = self.client.account.me()
        return dict(
            self.account_scope,
            balance_amount=str(Decimal(str(account.current_balance))),
            balance_unit="credits",
            fetched_at=now(),
            freshness="fresh",
        )

    def pages(self, factory):
        iterator = iter(factory())
        while True:
            with self.lock:
                try:
                    page = next(iterator)
                except StopIteration:
                    return
            yield page

    def resources(self, kind="all", cancel=None):
        sources = [
            ("verification", lambda: _iter_api_pages(self.client, _Action("GET", "/api/pub/v2/verifications"))),
            (
                "renewable",
                lambda: _iter_api_pages(self.client, _Action("GET", "/api/pub/v2/reservations/rental/renewable")),
            ),
            (
                "nonrenewable",
                lambda: _iter_api_pages(self.client, _Action("GET", "/api/pub/v2/reservations/rental/nonrenewable")),
            ),
        ]
        for source, factory in sources:
            if kind != "all" and source != kind and not (kind == "rental" and source != "verification"):
                continue
            for page in self.pages(factory):
                if cancel and cancel.is_set():
                    return
                for raw in page["data"]:
                    try:
                        yield number_record(raw, source, self.scope)
                    except (ValueError, TypeError, AttributeError):
                        self.warn("Malformed resource record; coverage incomplete")

    def messages(self, number=None, cancel=None, resource_id=None, resource_kind=None):
        if resource_kind == "rental":
            seen = set()
            for kind in ("renewable", "nonrenewable"):
                for message in self.messages(number, cancel, resource_id, kind):
                    if message["id"] not in seen:
                        seen.add(message["id"])
                        yield message
            return
        params = {}
        if number:
            params["to"] = number
        if resource_id:
            params["reservationId"] = resource_id
        if resource_kind:
            params["reservationType"] = ReservationType.from_api(resource_kind).to_api()
        for page in self.pages(lambda: _iter_api_pages(self.client, _Action("GET", "/api/pub/v2/sms"), params=params)):
            if cancel and cancel.is_set():
                return
            for raw in page["data"]:
                try:
                    message = message_record(raw)
                except (ValueError, TypeError, AttributeError):
                    self.warn("Malformed SMS record; coverage incomplete")
                    continue
                if message["created_at"] is None:
                    self.warn("SMS timestamp unavailable; timestamp filters exclude this record")
                if resource_kind:
                    message.update(
                        resource_id=resource_id, resource_kind=resource_kind, association_source="scoped_query"
                    )
                yield message

    def details(self, kind, identity):
        with self.lock:
            if kind == "verification":
                raw = self.client._perform_action(
                    _Action("GET", "/api/pub/v2/verifications/" + quote(identity, safe=""))
                ).data
            else:
                acceptance = self.client._perform_action(
                    _Action("GET", "/api/pub/v2/reservations/" + quote(identity, safe=""))
                ).data
                action = _read_link(self.client, acceptance)
                path = urlparse(action.href).path
                if "/reservations/rental/renewable/" in path:
                    kind = "renewable"
                elif "/reservations/rental/nonrenewable/" in path:
                    kind = "nonrenewable"
                else:
                    raise ValueError("Unrecognized rental details link")
                raw = self.client._perform_action(action).data
        record = number_record(raw, kind, self.scope)
        if kind == "renewable" and raw.get("billingCycleId"):
            from .models import timestamp

            try:
                with self.lock:
                    cycle = self.client.billing_cycles.get(raw["billingCycleId"])
                record["renews_at"] = timestamp(cycle.next_auto_renew_attempt)
            except Exception:
                record["renewal_detail_status"] = "unavailable"
        return record

    def quote(self, kind, request):
        with self.lock:
            # Pricing has separate schemas; use the existing SDK conversion.
            if kind == "verification":
                value = self.client.verifications.pricing(NewVerificationRequest.from_api(request.to_api()))
            else:
                # The legacy SDK pricing helper requires this deprecated value;
                # the pinned contract documents always-on receiving. Purchase
                # serialization still preserves the caller's original payload.
                pricing_data = dict(request.to_api(), alwaysOn=True)
                value = self.client.reservations.pricing(NewRentalRequest.from_api(pricing_data))
        return dict(
            amount=str(Decimal(str(value.price))),
            amount_unit=None,
            fetched_at=now(),
            price_protection="server" if kind == "verification" else "preflight_only",
        )

    def submit(self, kind, request):
        with self.lock:
            path = "/api/pub/v2/verifications" if kind == "verification" else "/api/pub/v2/reservations/rental"
            return self.client._perform_action(_Action("POST", path), json=request.to_api()).data

    def resolve(self, kind, acceptance):
        with self.lock:
            return self.client._perform_action(_read_link(self.client, acceptance)).data

    def services(self, kind):
        with self.lock:
            values = self.client.services.list(
                NumberType.MOBILE,
                ReservationType.VERIFICATION if kind == "verification" else ReservationType.NONRENEWABLE,
            )
        return [v.service_name for v in values]

    def cancel(self, identity):
        with self.lock:
            return self.client.verifications.cancel(identity)

    def wake(self, identity):
        with self.lock:
            return self.client.wake_requests.create(identity).to_api()

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def close(self):
        self.client.session.close()
