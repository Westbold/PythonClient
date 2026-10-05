"""Optional terminal application. Importing the SDK never imports UI frameworks."""


def main():
    import sys

    if sys.version_info < (3, 10):
        print("The optional terminal application requires Python 3.10 or newer", file=sys.stderr)
        return 2
    try:
        from .cli import run
    except ImportError as exc:
        if exc.name and exc.name.split(".")[0] in {
            "typer",
            "textual",
            "platformdirs",
            "keyring",
            "tomli",
            "jsonschema",
        }:
            print('Install the terminal extra: pip install "textverified[tui]"', file=sys.stderr)
            return 2
        raise
    return run()
