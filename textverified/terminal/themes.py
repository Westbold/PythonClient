"""Translate validated application themes to Textual themes."""
import dataclasses
import re
from .config import tomllib

TOKENS = {
    "background": "background",
    "foreground": "foreground",
    "surface": "surface",
    "muted": "secondary",
    "accent": "accent",
    "border": "primary",
    "focus": "accent",
    "success": "success",
    "warning": "warning",
    "error": "error",
    "unread": "accent",
    "header_background": "panel",
    "header_foreground": "foreground",
    "footer_background": "panel",
    "footer_foreground": "foreground",
    "selection_background": "primary",
    "selection_foreground": "foreground",
}


def load_theme(name, config):
    from textual.theme import Theme, BUILTIN_THEMES

    terminal = dataclasses.replace(
        BUILTIN_THEMES["textual-ansi"],
        name="terminal",
        dark=config.settings["appearance"]["terminal_polarity"] != "light",
    )
    builtins = {
        "terminal": terminal,
        "textverified-dark": Theme(
            name="textverified-dark",
            primary="#3b82f6",
            secondary="#94a3b8",
            accent="#60a5fa",
            background="#0b1220",
            foreground="#e2e8f0",
            surface="#111d30",
            panel="#16243b",
            warning="#efc66b",
            error="#f48282",
            success="#74c7b8",
            dark=True,
        ),
        "textverified-light": Theme(
            name="textverified-light",
            primary="#245c91",
            secondary="#596a79",
            accent="#2563eb",
            background="#fafbfc",
            foreground="#17232e",
            surface="#edf1f5",
            panel="#edf1f5",
            warning="#875c08",
            error="#a12222",
            success="#176c61",
            dark=False,
        ),
    }
    if name in builtins:
        return builtins[name]
    if not name.startswith("custom:") or not re.fullmatch(r"[A-Za-z0-9_-]+", name[7:]):
        raise ValueError("Unknown theme: " + name)
    path = config.directory / "themes" / (name[7:] + ".toml")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if set(data) - {"schema_version", "name", "base", "polarity", "colors", "styles"}:
        raise ValueError("Unknown custom theme setting")
    if data.get("schema_version") != 1 or data.get("name") != name[7:] or data.get("base", "terminal") not in builtins:
        raise ValueError("Invalid theme identity/base/schema_version")
    if data.get("polarity", "dark") not in ("dark", "light"):
        raise ValueError("Invalid theme polarity")
    colors = {}
    variables = {}
    for token, value in data.get("colors", {}).items():
        if (
            token not in TOKENS
            or not isinstance(value, str)
            or not re.fullmatch(
                r"default|ansi_(?:bright_)?(?:black|red|green|yellow|blue|magenta|cyan|white)|#[0-9a-fA-F]{6}", value
            )
        ):
            raise ValueError("Invalid color token: " + token)
        colors[TOKENS[token]] = "ansi_default" if value == "default" else value
        if token == "selection_background":
            variables["block-cursor-background"] = colors[TOKENS[token]]
    for token, value in data.get("styles", {}).items():
        if (
            token not in ("selection", "header", "footer")
            or not isinstance(value, str)
            or set(value.split()) - {"reverse", "bold", "underline", "normal", "italic"}
        ):
            raise ValueError("Invalid style: " + token)
        if token == "selection":
            variables["block-cursor-text-style"] = value
    base = builtins[data.get("base", "terminal")]
    return dataclasses.replace(
        base,
        name=name,
        dark=data.get("polarity", "dark") == "dark",
        variables=dict(base.variables, **variables),
        **colors,
    )
