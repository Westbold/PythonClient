"""Optional terminal app. The SDK does not import Rich."""
from textverified._version import __version__


def main(argv=None):
    import sys

    if sys.version_info < (3, 10):
        print("The terminal app requires Python 3.10 or newer.", file=sys.stderr)
        return 2
    try:
        from .cli import main as run
    except ModuleNotFoundError as error:
        if error.name != "rich" and not error.name.startswith("rich."):
            raise
        print('Install the terminal app with: pip install "textverified[tui]"', file=sys.stderr)
        return 2
    return run(argv)
