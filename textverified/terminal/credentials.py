"""Whole-pair environment credentials, then the local credential cache."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class CredentialError(Exception):
    pass


def cache_path() -> Path:
    override = os.environ.get("TEXTVERIFIED_CONFIG_DIR")
    base = (
        Path(override) / "cache"
        if override
        else Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "textverified"
    )
    return base / "credentials.json"


def from_environment() -> tuple[str, str] | None:
    user, key = os.environ.get("TEXTVERIFIED_API_USERNAME"), os.environ.get("TEXTVERIFIED_API_KEY")
    if user or key:
        if not (user and key):
            raise CredentialError("Set both TEXTVERIFIED_API_USERNAME and TEXTVERIFIED_API_KEY.")
        return user, key
    return None


def _records() -> dict:
    path = cache_path()
    if not path.exists():
        return {}
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, dict):
            raise ValueError()
        return records
    except (OSError, ValueError) as error:
        raise CredentialError("Couldn't read the credential cache; remove it and run `tv login` again.") from error


def load() -> tuple[tuple[str, str] | None, str | None]:
    found = from_environment()
    if found:
        return found, "environment"
    record = _records().get("default", {})
    if not isinstance(record, dict):
        raise CredentialError("Invalid credential cache; run `tv logout` then `tv login`.")
    user, key = record.get("api_username"), record.get("api_key")
    if user and key and isinstance(user, str) and isinstance(key, str):
        return (user, key), "cache"
    return None, None


def _write(records: dict) -> None:
    path = cache_path()
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".textverified-")
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(records, stream)
        Path(temporary).chmod(0o600)
        os.replace(temporary, path)
    except OSError as error:
        raise CredentialError("Couldn't save the credential cache; check its directory permissions.") from error
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


def save(user: str, key: str) -> None:
    records = _records()
    records["default"] = {"api_username": user, "api_key": key}
    _write(records)


def clear() -> bool:
    records = _records()
    if "default" not in records:
        return False
    del records["default"]
    if records:
        _write(records)
    else:
        try:
            cache_path().unlink()
        except OSError as error:
            raise CredentialError("Couldn't remove the credential cache.") from error
    return True
