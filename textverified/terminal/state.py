"""Metadata only: never persist SMS bodies, parsed codes or API credentials."""
import json
import sqlite3
import threading
from .config import private_directory


class State:
    def __init__(self, config, required=False):
        self.lock = threading.RLock()
        self.durable = True
        try:
            private_directory(config.state_directory)
            path = config.state_directory / "state.sqlite3"
            self.db = sqlite3.connect(str(path), timeout=3, check_same_thread=False)
            path.chmod(0o600)
        except (OSError, sqlite3.Error):
            if required:
                raise ValueError("State storage is unavailable; durable resume cannot be used")
            self.db = sqlite3.connect(":memory:", check_same_thread=False)
            self.durable = False
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            self.db.close()
            from .config import TerminalError

            raise TerminalError("Local state was written by a newer client", 7, "incompatible_state")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages(scope TEXT, id TEXT, digest TEXT, is_read INTEGER,
                PRIMARY KEY(scope,id));
            CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, scope TEXT, payload TEXT);
            CREATE TABLE IF NOT EXISTS checkpoints(scope TEXT, name TEXT, filters TEXT, payload TEXT,
                PRIMARY KEY(scope,name));
            PRAGMA user_version=1;
        """
        )

    def read(self, scope, identity):
        result = self.db.execute("SELECT is_read FROM messages WHERE scope=? AND id=?", (scope, identity)).fetchone()
        return result is not None and bool(result[0])

    def mark_read(self, scope, identity):
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO messages VALUES(?,?,NULL,1) ON CONFLICT(scope,id) DO UPDATE SET is_read=1",
                (scope, identity),
            )

    def receipt(self, scope, result):
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO receipts VALUES(?,?,?)", (result["operation_id"], scope, json.dumps(result))
            )

    def checkpoint(self, scope, name, filters, digests=None):
        if not self.durable:
            raise ValueError("Durable checkpoint storage is unavailable")
        if digests is not None:
            with self.lock, self.db:
                self.db.execute(
                    "INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,?)", (scope, name, filters, json.dumps(digests))
                )
            return
        row = self.db.execute(
            "SELECT filters,payload FROM checkpoints WHERE scope=? AND name=?", (scope, name)
        ).fetchone()
        if row and row[0] != filters:
            raise ValueError("Resume filters changed; use a new checkpoint name")
        return json.loads(row[1]) if row else None

    def observe(self, scope, messages, baseline):
        """Persist first-seen/read metadata, including unread state on restart."""
        from .sync import digest

        unread = set()
        with self.lock, self.db:
            for message in messages:
                self.db.execute(
                    "INSERT INTO messages VALUES(?,?,?,?) ON CONFLICT(scope,id) DO UPDATE SET digest=excluded.digest",
                    (scope, message["id"], digest(message), int(baseline)),
                )
                if not self.read(scope, message["id"]):
                    unread.add(message["id"])
        return unread

    def close(self):
        self.db.close()
