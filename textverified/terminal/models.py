"""Small normalized records and safe terminal text."""
import datetime as dt
import re
from decimal import Decimal
from dateutil.parser import isoparse

UTC = dt.timezone.utc
ACTIVE = {
    "verificationPending",
    "verificationReused",
    "verificationReactivated",
    "renewableActive",
    "nonrenewableActive",
}
HISTORY = {
    "verificationCompleted",
    "verificationCanceled",
    "verificationTimedOut",
    "verificationReported",
    "verificationRefunded",
    "renewableExpired",
    "renewableRefunded",
    "nonrenewableExpired",
    "nonrenewableRefunded",
}


def now():
    return dt.datetime.now(UTC).isoformat().replace("+00:00", "Z")


def timestamp(value, strict=False):
    if value is None:
        return None
    try:
        parsed = isoparse(value) if isinstance(value, str) else value
        if parsed.tzinfo is None:
            raise ValueError("Timestamp must include a timezone")
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError, AttributeError):
        if strict:
            raise ValueError("Use an RFC 3339 timestamp with an offset or Z")
        return None


def text(value):
    return None if value is None else str(value)


def safe(value):
    """Strip terminal controls (including OSC/CSI) while preserving ordinary text."""
    value = str(value) if value is not None else "Unknown"
    value = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", value)
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)
    return "".join(c for c in value if c in "\n\t" or (ord(c) >= 32 and not 127 <= ord(c) <= 159))


def number_record(raw, kind, scope):
    if not isinstance(raw, dict) or not raw.get("id"):
        raise ValueError("Resource record has no ID")
    state = text(raw.get("state"))
    lifecycle = "active" if state in ACTIVE else "history" if state in HISTORY else "attention"
    return dict(
        key=scope + "|" + kind + "|" + str(raw["id"]),
        kind=kind,
        resource_id=str(raw["id"]),
        number=text(raw.get("number")),
        service=text(raw.get("serviceName")),
        raw_state=state,
        lifecycle=lifecycle,
        created_at=timestamp(raw.get("createdAt")),
        expires_at=timestamp(raw.get("endsAt")),
        renews_at=None,
        receiving_readiness="always_on" if raw.get("alwaysOn") is True else "unknown",
        renewal_enabled=raw.get("isIncludedForNextRenewal"),
        last_activity_at=None,
        available_actions=(
            ["cancel"]
            if kind == "verification" and lifecycle == "active" and raw.get("cancel", {}).get("canCancel")
            else ["wake"]
            if kind != "verification" and lifecycle == "active" and raw.get("alwaysOn") is False
            else []
        ),
        fetched_at=now(),
    )


def message_record(raw):
    if not isinstance(raw, dict) or not raw.get("id"):
        raise ValueError("SMS record has no ID")
    body = text(raw.get("smsContent"))
    return dict(
        id=str(raw["id"]),
        created_at=timestamp(raw.get("createdAt")),
        observed_at=now(),
        to_number=text(raw.get("to")),
        from_number=text(raw.get("from")),
        body=body,
        parsed_code=text(raw.get("parsedCode")),
        content_state="available"
        if body is not None
        else "encrypted"
        if raw.get("encrypted") is True
        else "unavailable",
        resource_kind="unknown",
        resource_id=None,
        service=None,
        association_source="unknown",
    )


def sort_number(record):
    verification = record["kind"] == "verification"
    group = (
        (0 if verification else 1)
        if record["lifecycle"] == "active"
        else 2
        if record["lifecycle"] == "attention"
        else 3
        if verification
        else 4
    )
    deadline = record.get("expires_at") or record.get("renews_at")
    created = record.get("last_activity_at") or record.get("created_at")
    descending = -isoparse(created).timestamp() if created else float("inf")
    return group, (deadline is None, deadline or "") if group < 2 else (False, ""), descending, record["key"]


def time_label(record):
    deadline = record.get("expires_at") or record.get("renews_at")
    if not deadline:
        return "Time unavailable"
    if record["kind"] != "verification":
        return ("Expires " if record.get("expires_at") else "Renews ") + isoparse(deadline).astimezone().strftime(
            "%b %d %H:%M"
        )
    if record["lifecycle"] != "active":
        return isoparse(deadline).astimezone().strftime("%b %d %H:%M")
    seconds = max(0, int((isoparse(deadline) - dt.datetime.now(UTC)).total_seconds()))
    if seconds == 0:
        return "00:00 - checking status"
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return ("%02d:" % hours if hours else "") + "%02d:%02d" % (minutes, seconds)


def matches(record, query):
    if not query:
        return True
    haystack = " ".join(str(v) for v in record.values() if v is not None).casefold()
    query = query.casefold()
    digits = re.sub(r"\D", "", query)
    return query in haystack or (
        len(digits) >= 3
        and all(c.isdigit() or c in "+()- ." for c in query)
        and any(digits in re.sub(r"\D", "", str(record.get(k) or "")) for k in ("number", "to_number", "from_number"))
    )


def state_label(record):
    raw = record.get("raw_state")
    if raw is None:
        return "State unknown"
    label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw).capitalize()
    if record["lifecycle"] == "attention":
        label += " (needs attention)"
    if record["kind"] != "verification":
        label += " / " + {"always_on": "Always-on", "unknown": "Readiness unknown"}.get(
            record["receiving_readiness"], record["receiving_readiness"]
        )
    return label


def group_label(record):
    if record["lifecycle"] == "attention":
        return "Needs attention"
    product = "verification" if record["kind"] == "verification" else "rental"
    return ("Active " + product) if record["lifecycle"] == "active" else product.capitalize() + " history"
