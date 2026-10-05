"""Generate command reference from actual help without authentication."""
import os
import subprocess
import sys
from pathlib import Path

COMMANDS = [
    [],
    ["tui"],
    ["auth"],
    ["auth", "login"],
    ["auth", "status"],
    ["auth", "logout"],
    ["account", "show"],
    ["list"],
    ["verification", "list"],
    ["verification", "get"],
    ["verification", "quote"],
    ["verification", "buy"],
    ["verification", "cancel"],
    ["rental", "list"],
    ["rental", "get"],
    ["rental", "quote"],
    ["rental", "buy"],
    ["rental", "wake"],
    ["sms", "list"],
    ["sms", "watch"],
    ["sms", "wait"],
    ["schema", "show"],
    ["theme", "list"],
    ["theme", "set"],
    ["config", "path"],
    ["config", "show"],
    ["config", "validate"],
]

if __name__ == "__main__":
    env = dict(os.environ, NO_COLOR="1", COLUMNS="100", TERM="dumb", PYTHONIOENCODING="utf-8")
    parts = [
        "CLI reference",
        "=============",
        "",
        "Generated with ``python generate_terminal_docs.py`` from implemented help.",
        "Root options precede subcommands. Static shell completion needs no credentials:",
        "``textverified --install-completion`` or ``textverified --show-completion``.",
        "",
    ]
    for command in COMMANDS:
        title = "textverified" + (" " + " ".join(command) if command else "")
        result = subprocess.run(
            [sys.executable, "-m", "textverified.terminal", *command, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            env=env,
        )
        # Remove the runtime module path from the reviewable command examples.
        help_text = result.stdout.replace("python -m textverified.terminal", "textverified")
        parts.extend([title, "-" * len(title), "", ".. code-block:: text", ""])
        parts.extend(("   " + line.rstrip()) if line.strip() else "" for line in help_text.strip().splitlines())
        parts.append("")
    Path("docs/terminal-cli.rst").write_text("\n".join(parts) + "\n", encoding="utf-8")
