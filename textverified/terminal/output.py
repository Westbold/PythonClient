"""Finite JSON is spooled before stdout; streams flush complete records."""
import json
import sys
import tempfile
from .models import now, safe


class ReplaySpool:
    """Private temporary ordering spool, removed on success/error/interrupt."""

    def __init__(self):
        import sqlite3
        from pathlib import Path

        self.directory = tempfile.TemporaryDirectory(prefix="textverified-replay-")
        Path(self.directory.name).chmod(0o700)
        path = Path(self.directory.name) / "replay.sqlite3"
        self.db = sqlite3.connect(str(path))
        path.chmod(0o600)
        self.db.execute("CREATE TABLE replay(id TEXT PRIMARY KEY, created TEXT, body TEXT)")

    def add(self, message):
        self.db.execute(
            "INSERT OR REPLACE INTO replay VALUES(?,?,?)",
            (message["id"], message["created_at"] or "", json.dumps(message)),
        )

    def records(self):
        for row in self.db.execute("SELECT body FROM replay ORDER BY created,id"):
            yield json.loads(row[0])

    def close(self):
        self.db.close()
        self.directory.cleanup()


def emit(value):
    print(json.dumps(value, ensure_ascii=True), flush=True)


def event(account, name, record, replay=False):
    return dict(
        schema_version=1,
        event=name,
        replay=replay,
        account=account,
        observed_at=record.get("observed_at", now()),
        **({"message": record} if name.startswith("sms.") else {"resource": record}),
    )


def finite(records, account, format="table", limit=100, sms=False, warnings=None):
    if format not in ("table", "json", "ndjson"):
        raise ValueError("Format must be table, json or ndjson")
    count, complete = 0, True
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as spool:
        for record in records:
            if limit is not None and count >= limit:
                complete = False
                break
            if format == "ndjson":
                emit(event(account, "sms.received" if sms else "resource.snapshot", record, replay=True))
            else:
                if count:
                    spool.write("," if format == "json" else "\n")
                if format == "json":
                    spool.write(json.dumps(record, ensure_ascii=True))
                elif sms:
                    spool.write(
                        safe(
                            " | ".join(
                                str(record.get(k) or "")
                                for k in ("created_at", "to_number", "from_number", "body", "parsed_code")
                            )
                        ).replace("\n", " ")
                    )
                else:
                    spool.write(
                        safe(
                            " | ".join(
                                str(record.get(k) or "")
                                for k in ("kind", "resource_id", "service", "number", "raw_state", "expires_at")
                            )
                        )
                    )
            count += 1
        if format == "json":
            envelope = dict(
                schema_version=1,
                account=account,
                meta=dict(
                    scope="account",
                    history_scope="api_available",
                    requested_limit=limit,
                    returned=count,
                    scan_complete=complete and not any("incomplete" in str(w) for w in (warnings or [])),
                    has_more=not complete,
                    fetched_at=now(),
                    snapshot_consistency="best_effort",
                    warnings=warnings or [],
                ),
            )
            prefix = json.dumps(envelope, ensure_ascii=True)[:-1]
            sys.stdout.write(prefix + ', "items":[')
        spool.seek(0)
        if format != "ndjson":
            while True:
                chunk = spool.read(65536)
                if not chunk:
                    break
                sys.stdout.write(chunk)
            sys.stdout.write("]}\n" if format == "json" else "\n")
            sys.stdout.flush()
