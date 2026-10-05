"""Shared read and consequential-action workflows."""
from decimal import Decimal
import threading
import uuid
import requests
import sqlite3
from textverified.exceptions import TextVerifiedError
from .config import TerminalError
from .fields import validate
from .models import sort_number
from .sync import Feed


class Application:
    def __init__(self, adapter, config, state):
        self.adapter, self.config, self.state = adapter, config, state
        self.feed = Feed(adapter, int(config.settings["storage"]["max_in_memory_messages"]))
        self.generation = 0
        self.cancelled = threading.Event()
        self.mutation_lock = threading.Lock()

    def numbers(self, kind="all", hydrate=True):
        rows = {row["key"]: row for row in self.adapter.resources(kind, self.cancelled)}
        if hydrate:
            for key, row in list(rows.items()):
                if row["lifecycle"] == "active":
                    try:
                        rows[key] = self.adapter.details(row["kind"], row["resource_id"])
                    except Exception:
                        row["detail_status"] = "unavailable"
        return sorted(rows.values(), key=sort_number)

    def quote(self, kind, inputs, max_price=None, require_cap=False):
        if require_cap and kind != "verification":
            raise TerminalError(
                "Rental purchases have no documented server price cap", 7, "unsupported_price_protection"
            )
        request = validate(kind + ".buy", inputs)
        cap = max_price if max_price is not None else request.data.get("maxPrice")
        if require_cap and cap is None:
            raise ValueError("--require-server-price-cap requires a maximum price")
        if cap is not None and (not Decimal(str(cap)).is_finite() or Decimal(str(cap)) < 0):
            raise ValueError("Maximum price must be a finite nonnegative amount")
        quote = self.adapter.quote(kind, request)
        if cap is not None and Decimal(quote["amount"]) > Decimal(str(cap)):
            raise TerminalError("Quote exceeds maximum price", 5, "price_limit_exceeded")
        return request, quote

    def buy(self, kind, request, quote):
        if not self.mutation_lock.acquire(blocking=False):
            raise TerminalError("A mutation is already in progress")
        result = dict(
            outcome="submitting",
            operation_id=str(uuid.uuid4()),
            resource_ids=[],
            sale_id=None,
            quoted_amount=quote["amount"],
            actual_amount=None,
            amount_unit=quote["amount_unit"],
            price_protection=quote["price_protection"],
            detail_status="pending",
            error=None,
        )
        try:
            if not self.state.durable:
                raise TerminalError("Receipt storage is unavailable; restore state directory access before purchasing")
            self.write_receipt(result)
            try:
                acceptance = self.adapter.submit(kind, request)
            except TextVerifiedError as exc:
                if "HTTP 5" in exc.context:
                    result.update(
                        outcome="unknown",
                        error="Server failed after possible submission; inspect resources before retrying",
                    )
                    self.write_receipt(result)
                    raise TerminalError(
                        "Purchase outcome unknown; operation " + result["operation_id"], 9, "purchase_outcome_unknown"
                    )
                result.update(outcome="rejected", error="API rejected purchase")
                self.write_receipt(result)
                raise TerminalError("API rejected purchase; review inputs and balance", 5, "purchase_rejected")
            except (requests.RequestException, ValueError, KeyError, KeyboardInterrupt):
                result.update(
                    outcome="unknown",
                    error="Submission may have completed. Inspect recent resources and this receipt before retrying.",
                )
                self.write_receipt(result)
                raise TerminalError(
                    "Purchase outcome unknown; operation "
                    + result["operation_id"]
                    + "; inspect account and receipt before retrying",
                    9,
                    "purchase_outcome_unknown",
                )
            result["outcome"] = "accepted"
            self.write_receipt(result)
            try:
                details = self.adapter.resolve(kind, acceptance)
                if kind == "verification":
                    result["resource_ids"] = [str(details["id"])]
                    result["actual_amount"] = (
                        str(Decimal(str(details["totalCost"]))) if details.get("totalCost") is not None else None
                    )
                else:
                    result["resource_ids"] = [str(r["id"]) for r in details.get("reservations", [])]
                    result["sale_id"] = str(details["id"]) if details.get("id") is not None else None
                result.update(outcome="created", detail_status="available")
            except (Exception, KeyboardInterrupt):
                result.update(detail_status="pending", error="Accepted; details unavailable. Do not purchase again.")
            self.write_receipt(result)
            return result
        finally:
            self.mutation_lock.release()

    def mutate(self, kind, identity):
        if not self.mutation_lock.acquire(blocking=False):
            raise TerminalError("A mutation is already in progress")
        receipt = dict(operation_id=str(uuid.uuid4()), outcome="submitting", action=kind, resource_ids=[identity])
        try:
            if not self.state.durable:
                raise TerminalError("Receipt storage unavailable; restore access before a mutation")
            self.write_receipt(receipt)
            try:
                result = self.adapter.cancel(identity) if kind == "cancel" else self.adapter.wake(identity)
            except TextVerifiedError:
                receipt["outcome"] = "rejected"
                self.write_receipt(receipt)
                raise TerminalError("API rejected operation", 5, "mutation_rejected")
            except (Exception, KeyboardInterrupt):
                receipt["outcome"] = "unknown"
                self.write_receipt(receipt)
                raise TerminalError(
                    "Operation outcome unknown; inspect resource before retrying", 9, "mutation_outcome_unknown"
                )
            receipt["outcome"] = "accepted"
            self.write_receipt(receipt)
            return result
        finally:
            self.mutation_lock.release()

    def write_receipt(self, result):
        try:
            self.state.receipt(self.adapter.scope, result)
        except (OSError, sqlite3.Error):
            status = 2 if result["outcome"] == "submitting" else 9
            raise TerminalError(
                "Cannot persist operation receipt " + result["operation_id"] + "; inspect account before retrying",
                status,
                "receipt_storage_failed",
            )

    def close(self):
        self.cancelled.set()
        self.adapter.close()
        self.state.close()
