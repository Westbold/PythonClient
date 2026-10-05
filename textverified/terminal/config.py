"""Validated local configuration and whole-pair credential resolution."""
import os
import json
import re
import tempfile
from pathlib import Path
import platformdirs

try:
    import tomllib
except ImportError:
    import tomli as tomllib

DEFAULTS = {
    "account": {"default_profile": ""},
    "ui": {
        "initial_view": "numbers",
        "show_clock": True,
        "clock_seconds": False,
        "timezone": "local",
        "mouse": True,
        "bell": False,
        "history_collapsed": True,
    },
    "appearance": {"theme": "textverified-dark", "terminal_polarity": "auto", "color": "auto", "style_file": ""},
    "sync": {
        "sms_interval_seconds": 3,
        "verification_interval_seconds": 10,
        "resources_interval_seconds": 30,
        "rental_details_interval_seconds": 60,
        "account_interval_seconds": 60,
        "request_timeout_seconds": 15,
        "backoff_max_seconds": 60,
    },
    "cli": {"list_limit": 100, "watch_tail": 20, "wait_timeout_seconds": 120},
    "storage": {"persist_read_markers": True, "max_in_memory_messages": 10000, "metadata_retention_days": 90},
}


class TerminalError(Exception):
    def __init__(self, message, status=2, code="invalid_input", retryable=False):
        super().__init__(message)
        self.status, self.code, self.retryable = status, code, retryable


def private_directory(path):
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def atomic_write(path, contents):
    private_directory(path.parent)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".textverified-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(contents)
        Path(name).chmod(0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def dump_toml(data):
    lines = []

    def section(values, prefix=""):
        scalars = {k: v for k, v in values.items() if not isinstance(v, dict)}
        if prefix:
            lines.append("[" + prefix + "]")
        import json

        for key, value in scalars.items():
            lines.append(key + " = " + (str(value).lower() if isinstance(value, bool) else json.dumps(value)))
        lines.append("")
        for key, value in values.items():
            if isinstance(value, dict):
                section(value, prefix + "." + key if prefix else key)

    section(data)
    return "\n".join(lines)


class Config:
    def __init__(self):
        override = os.environ.get("TEXTVERIFIED_CONFIG_DIR")
        self.directory = (
            Path(override) if override else Path(platformdirs.user_config_dir("textverified", appauthor=False))
        )
        self.state_directory = (
            Path(override) / "state" if override else Path(platformdirs.user_state_dir("textverified", appauthor=False))
        )
        self.path = self.directory / "config.toml"
        self.cache_directory = (
            Path(override) / "cache"
            if override
            else Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "textverified"
        )
        self.credentials_path = self.cache_directory / "credentials.json"
        self.raw = tomllib.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        import copy

        self.settings = copy.deepcopy(DEFAULTS)
        if self.raw.get("schema_version", 1) != 1:
            raise ValueError("config.toml: unsupported schema_version")
        for section, values in self.raw.items():
            if section in ("schema_version", "profiles"):
                continue
            if section not in DEFAULTS or not isinstance(values, dict):
                raise ValueError("config.toml: unknown section " + section)
            for key, value in values.items():
                if key not in DEFAULTS[section]:
                    raise ValueError("config.toml: unknown setting " + section + "." + key)
                expected = DEFAULTS[section][key]
                if isinstance(expected, bool) and not isinstance(value, bool):
                    raise ValueError("Expected boolean: " + section + "." + key)
                if isinstance(expected, str) and not isinstance(value, str):
                    raise ValueError("Expected string: " + section + "." + key)
                if type(expected) is int and (
                    isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0
                ):
                    raise ValueError("Expected positive number: " + section + "." + key)
                self.settings[section][key] = value
        for section in ("cli", "storage"):
            for key in ("list_limit", "watch_tail", "max_in_memory_messages", "metadata_retention_days"):
                if key in self.settings[section] and type(self.settings[section][key]) is not int:
                    raise ValueError("Expected integer: " + section + "." + key)
        self.profiles = self.raw.get("profiles", {})
        if not isinstance(self.profiles, dict):
            raise ValueError("profiles must be a table")
        for name, profile in self.profiles.items():
            self.check_profile_name(name)
            if not isinstance(profile, dict):
                raise ValueError("Profile must be a table: " + name)
            if (
                set(profile) - {"api_username", "credential_ref", "credential_store"}
                or not profile.get("api_username")
                or profile.get("credential_ref") != "textverified/" + name
                or profile.get("credential_store", "keyring") not in ("keyring", "cache")
            ):
                raise ValueError("Invalid profile reference: " + name)
        if self.settings["ui"]["initial_view"] not in ("numbers", "inbox"):
            raise ValueError("Invalid initial_view")
        if self.settings["appearance"]["terminal_polarity"] not in ("auto", "dark", "light"):
            raise ValueError("Invalid terminal_polarity")
        if self.settings["appearance"]["color"] not in ("auto", "always", "never"):
            raise ValueError("Invalid color policy")
        if self.settings["ui"]["timezone"] != "local":
            from zoneinfo import ZoneInfo

            try:
                ZoneInfo(self.settings["ui"]["timezone"])
            except (KeyError, ValueError):
                raise ValueError("Invalid display timezone")

    @staticmethod
    def check_profile_name(name):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
            raise ValueError("Profile names use letters, digits, underscore and hyphen")

    def save(self):
        atomic_write(self.path, dump_toml(self.raw))

    def cached_credentials(self):
        if not self.credentials_path.exists():
            return {}
        try:
            records = json.loads(self.credentials_path.read_text(encoding="utf-8"))
            if not isinstance(records, dict) or any(
                not isinstance(record, dict)
                or set(record) != {"api_username", "api_key"}
                or not all(isinstance(value, str) and value for value in record.values())
                for record in records.values()
            ):
                raise ValueError("Invalid credential cache")
            return records
        except (ValueError, OSError):
            raise TerminalError("Credential cache unavailable; log in again", 3, "credential_store_unavailable")

    def save_credentials(self, user, key, profile="default"):
        self.check_profile_name(profile)
        records = self.cached_credentials()
        records[profile] = {"api_username": user, "api_key": key}
        atomic_write(self.credentials_path, json.dumps(records))
        self.profiles[profile] = dict(
            api_username=user, credential_ref="textverified/" + profile, credential_store="cache"
        )
        self.raw["profiles"] = self.profiles
        self.raw.setdefault("account", {})["default_profile"] = profile
        self.settings["account"]["default_profile"] = profile
        self.save()

    def remove_credentials(self, profile="default"):
        self.check_profile_name(profile)
        record = self.profiles.get(profile)
        if not record:
            return
        if record.get("credential_store") == "cache":
            records = self.cached_credentials()
            records.pop(profile, None)
            if records:
                atomic_write(self.credentials_path, json.dumps(records))
            else:
                self.credentials_path.unlink(missing_ok=True)
        else:
            import keyring

            keyring.delete_password(record["credential_ref"], record["api_username"])
        del self.profiles[profile]
        self.raw["profiles"] = self.profiles
        if self.settings["account"]["default_profile"] == profile:
            self.raw.setdefault("account", {})["default_profile"] = ""
            self.settings["account"]["default_profile"] = ""
        self.save()

    def credentials(self, profile=None):
        explicit = profile is not None
        user, key = os.environ.get("TEXTVERIFIED_API_USERNAME"), os.environ.get("TEXTVERIFIED_API_KEY")
        if not explicit and (user or key):
            if not (user and key):
                raise TerminalError(
                    "Set both TEXTVERIFIED_API_USERNAME and TEXTVERIFIED_API_KEY", 3, "authentication_required"
                )
            return user, key, None
        selected = profile or self.settings["account"]["default_profile"]
        if selected:
            record = self.profiles.get(selected)
            if record:
                try:
                    if record.get("credential_store") == "cache":
                        cached = self.cached_credentials().get(selected, {})
                        secret = cached.get("api_key") if cached.get("api_username") == record["api_username"] else None
                    else:
                        import keyring

                        secret = keyring.get_password(record["credential_ref"], record["api_username"])
                except Exception:
                    raise TerminalError(
                        "Credential store unavailable; use environment credentials", 3, "credential_store_unavailable"
                    )
                if secret:
                    return record["api_username"], secret, selected
        raise TerminalError(
            "Authentication required: set environment credentials or run textverified auth login",
            3,
            "authentication_required",
        )
