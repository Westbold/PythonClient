Terminal client
===============

Installation
------------

Install the optional TUI/CLI extra, using Python 3.10 or newer:

.. code-block:: bash

   pip install "textverified[tui]"

For development: ``pip install -e ".[tui]"``. Plain ``pip install textverified``
installs the SDK without terminal dependencies. The executable is
``textverified``; ``python -m textverified.terminal`` is equivalent.

Authentication
--------------

Supply a complete environment credential pair:

.. code-block:: bash

   export TEXTVERIFIED_API_USERNAME="your_username"
   export TEXTVERIFIED_API_KEY="your_api_key"
   textverified tui

In PowerShell use ``$env:TEXTVERIFIED_API_USERNAME = "your_username"`` and
``$env:TEXTVERIFIED_API_KEY = "your_api_key"``. Alternatively:

.. code-block:: bash

   textverified auth login
   textverified account show
   textverified tui

The TUI asks only for Email and API key, masks the key, validates the account
and saves credentials automatically for the next session. CLI login asks the
same two questions; ``--profile NAME`` optionally saves a named account.
Credentials are stored as local plaintext in
``~/.cache/textverified/credentials.json``, or under ``$XDG_CACHE_HOME`` when set.
The cache directory and file use owner-only permissions on Unix.
``textverified auth logout`` removes the default account; use ``--profile NAME``
for a named account. Existing OS-keyring profiles remain readable.
Configuration stores only a username and credential reference. An explicit
profile takes precedence over environment credentials as a whole pair. Without
an explicit profile, a complete environment pair precedes the default profile.
Partial credentials fail; pairs are never assembled from different sources.
Headless/SSH users can use environment credentials without a credential store.
Noninteractive commands never prompt. API keys are not command-line arguments.

Interactive tour
----------------

Numbers combines verifications and both rental kinds, ordered active
verifications, active rentals, attention, verification history, rental history.
Timers are painted locally; zero means checking status, and absent deadlines
say Time unavailable. Renewable dates come from the associated billing cycle.
Inbox displays separate Code and Body columns. Opening a row shows the full
message with readable sender, recipient and time details. Account, resource,
purchase review and receipt dialogs use labeled summaries.
Inbox uses the account-wide SMS endpoint independently of Numbers selection,
including retained inactive/external resource messages. Unknown association is
visible. A telephone-number match is labeled approximate, never an exact ID.

Use 1/2 to change views, Up/Down to move, Enter for full details and Tab to change
focus. Up from the first Numbers row reaches the purchase strip. Press v/r to
open a purchase form, / for literal search, f for search scope and ? for help.
Advanced JSON exposes schema fields; Fields shows allowed values. Changing
inputs invalidates an in-flight quote. Review focuses Back and requires deliberate
confirmation; repeated activation cannot dispatch the mutation twice.

Press c/n/y for code/number/body copying, g to follow newest messages, a for
supported explicit cancel/wake actions, F5 to refresh, Ctrl+P for account/profile/
theme actions and q to quit. Letter shortcuts are disabled in editable fields.
No wake, purchase, renewal, reply or server mark-read operation runs from a view.
Opening a message marks it read locally. Notifications remain inside the app.

Selection is anchored to IDs across refreshes. Reading older messages pauses
following; arrivals increment the new-message count. Full details retain all
text, sanitize terminal controls and display markup literally. Clipboard requests
use terminal support (OSC52); acceptance cannot be verified, particularly over
SSH/tmux. Selectable detail text is the fallback.

Loaded search filters current records immediately. All API history scans the
available pages, with progress and incomplete status after cancellation/error.
The TUI retains a bounded result window; refine the search or use CLI --all for
an exhaustive export. Esc cancels a history scan or closes a detail/search level.
At short screen heights details open in a modal; below 60 columns or 16 rows,
resize or use ordinary CLI commands.

Commands and safeguards
-----------------------

.. code-block:: bash

   textverified list --state active
   textverified sms list --all --json
   textverified sms list --query "sign-in" --limit 20
   textverified sms watch --format ndjson
   textverified sms watch --tail 0 --format ndjson
   textverified sms wait --id RESOURCE_ID --kind verification --code-only
   textverified schema show rental.buy
   textverified verification quote --service SERVICE
   textverified verification buy --service SERVICE --max-price 1.00 --yes --json
   textverified rental quote --service SERVICE --duration 30d --no-renewable
   textverified verification cancel RESOURCE_ID --yes
   textverified rental wake RESOURCE_ID --yes

SERVICE and RESOURCE_ID are placeholders. Renewable rentals require deliberate
selection. Quotes do not reserve inventory. Verification maximum prices are
server-enforced by the pinned contract. Rental caps are preflight only;
--require-server-price-cap fails before a rental purchase. The current rental
schema deprecates alwaysOn and documents always-on receiving; no sleeping state
is inferred from false alone. All financial operations create metadata receipts.
Accepted/details-pending results never trigger another purchase. Outcome unknown
returns exit 9: inspect recent resources and receipts before retrying.

Profiles, configuration and local state
---------------------------------------

``config path`` prints the platform configuration/state paths. XDG locations are
honored through platformdirs; TEXTVERIFIED_CONFIG_DIR overrides these locations and puts credentials in its
``cache/`` subdirectory. ``config path`` also prints the credential cache path.
The working directory is not an implicit credential or settings store.

.. code-block:: toml

   schema_version = 1

   [account]
   default_profile = "work"

   [ui]
   initial_view = "numbers"
   show_clock = true
   timezone = "local"

   [appearance]
   theme = "textverified-dark"
   terminal_polarity = "dark"
   style_file = ""

   [sync]
   sms_interval_seconds = 3
   resources_interval_seconds = 30
   verification_interval_seconds = 10
   account_interval_seconds = 60
   request_timeout_seconds = 15

   [storage]
   max_in_memory_messages = 10000
   persist_read_markers = true

``config show`` reports resolved nonsecret settings; ``config validate`` validates
settings, themes and optional TCSS. Unknown setting names and invalid bounds
fail visibly. Theme set writes configuration atomically. SQLite holds read
markers, watcher checkpoints and operation receipts; no plaintext SMS bodies,
parsed codes or API keys are archived. Missing/unwritable storage allows ordinary
reads with session-only state, but durable resume and mutations fail visibly.

Troubleshooting and privacy
---------------------------

If textverified is absent, install textverified[tui] in the Python environment
on PATH, or use python -m textverified.terminal. Redirected output should use
list/watch/wait rather than tui. No-argument invocation opens the TUI only on
interactive input/output; otherwise it prints help without authentication.

Restore default appearance with ``textverified tui --reset-style`` or
``textverified theme set terminal``. API errors retain stale data; an account
refresh cannot conceal an unhealthy SMS feed. SMS reconciliation scans all
retained pages because the schema provides no stable incremental cursor.
Large accounts may have an effective cadence slower than the nominal 3 seconds.
Server-deleted SMS cannot be recovered. Exports intentionally contain SMS data;
keep redirected output private. Temporary JSON/replay spools are removed after
normal completion, failure or interruption.

See :doc:`terminal-output`, :doc:`terminal-themes`, :doc:`terminal-maintenance`,
:doc:`terminal-testing`, and the :download:`API compatibility record <api-compatibility.md>`.
