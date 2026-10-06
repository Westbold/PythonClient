Terminal app
============

Installation
------------

The optional terminal app requires Python 3.10 or newer:

.. code-block:: bash

   pip install "textverified[tui]"

For this checkout: ``pip install -e ".[tui]"``. ``tv`` and ``textverified`` run
the same app; ``python -m textverified.terminal`` is the module entry point.
The extra adds Rich only. Importing the SDK does not load the terminal package.

Real account
------------

.. code-block:: bash

   tv login
   tv balance
   tv services discord
   tv --mock verify discord
   tv verify discord
   tv logout

Login asks for Email and a hidden API key; ``--email EMAIL`` can prefill email.
Validation happens before saving to ``~/.cache/textverified/credentials.json``.
``XDG_CACHE_HOME`` changes the cache root. ``TEXTVERIFIED_CONFIG_DIR`` instead
uses its ``cache/`` subdirectory. The default cached account from v0 is readable.
Logout removes it. Cached secrets are plaintext; Unix directory/file permissions
are 0700/0600, and writes are atomic. Keys are never command-line arguments.

A complete ``TEXTVERIFIED_API_USERNAME`` / ``TEXTVERIFIED_API_KEY`` pair
precedes the cache. Partial environment credentials fail rather than mixing
accounts. In PowerShell, set these with ``$env:TEXTVERIFIED_API_USERNAME =
"EMAIL"`` and ``$env:TEXTVERIFIED_API_KEY = "KEY"``.

``--mock`` sets the SDK client's ``TestMode.MOCK_SUCCESS``. Pricing and
verification/rental creation use the server-backed mock success scenario, and subsequent
requests follow the returned mock resource through the SDK. This does not purchase
a real number. Credentials and network access are required. Both modes search the
same API service catalog; account and balance requests still read your real account. Real purchases require confirmation or ``--yes`` for
scripts; the quoted price becomes the SDK's ``max_price``. Ctrl+C while waiting
refreshes cancellation eligibility before offering cancellation or continued
waiting. Partial service names, spelling suggestions and numbered choices are
supported. Prices are fetched for short service lists. SMS polling uses exact
reservation ID/type filters every three seconds.

Piped verification output is plain status lines ending with the bare code. Interactive output
uses an animated waiting card and an OSC 52 clipboard request. All branding
uses Unicode: the filled blue logo, four dancing white bars and a braille mark. No images, graphics
protocols, terminal background queries or image-generation tools are needed.
``--no-animation`` / ``TV_NO_ANIMATION=1`` disables animation; ``TV_THEME=light``
selects light-terminal colors. Half-blocks work with standard terminal fonts;
finer sextants are selected on supported terminals. Override with
``TV_BADGE=blocky`` or ``TV_BADGE=fine``. Rich honors ``NO_COLOR`` in auto mode. An explicit ``--color=always`` overrides it on a terminal. Global flags precede
commands. Use ``tv --help`` or ``tv verify --help`` for options.

Color and redirected output
---------------------------

.. code-block:: bash

   tv inbox > inbox.tsv
   tv poll --follow --timeout -1 | tee messages.tsv
   tv --color=always inbox
   tv --color=never inbox

``--color=auto`` is the default: terminal colors are detected automatically.
``--color=always`` forces ANSI colors on a terminal. ``--color=never``
disables colors. These are global flags, placed before the command.

Colors, animation and cursor redraws require stdout to be a real terminal.
Pipes and redirected files remain plain even with ``--color=always``. Inbox and polling retain
terminal tables and transient waiting animations when interactive; redirected
output uses tab-separated records. ``--no-animation`` also disables waiting
spinners on a terminal.

See :doc:`terminal_scripting` for CSV-aware stream consumers, inbox archives,
verification code capture and pipeline error handling.

Unified SMS inbox and polling
-----------------------------

All commands accepting ``--limit`` also accept ``--offset N`` (default 0).
Offsets are nonnegative counts of matching entries to skip before applying the
limit. Filters run first. Verification, rental and inbox candidates are sorted
newest first; rental offsets apply once across the merged rental types. Service
offsets apply to the alphabetical filtered catalog. Examples:

.. code-block:: bash

   tv inbox --offset 5 --limit 5
   tv verifications list --offset 5 --limit 5
   tv rentals list --offset 5 --limit 5
   tv services --offset 5 --limit 5
   tv rentals services gmail --offset 5 --limit 5

History queries fetch at most ``offset + limit`` candidates per feed through
SDK pagination. Larger offsets can require more API requests. These are views
of a changing account, rather than stable cursors: new entries between commands
can shift offsets. Offsets beyond the end succeed with no data rows.

.. code-block:: bash

   tv inbox
   tv inbox --limit 100 --since 2026-10-05T00:00:00Z
   tv inbox --line-number 14155550123
   tv inbox --reservation-id VERIFICATION_ID --type verification
   tv inbox --line-id RENTAL_ID --type renewable
   tv poll --timeout 60
   tv poll --line-number 14155550123
   tv poll --line-id RENTAL_ID --type nonrenewable
   tv poll --reservation-id VERIFICATION_ID --type verification
   tv poll --follow --timeout -1

Inbox summary columns include destination, sender, parsed code, body preview
and local received time as the final column. Message IDs and full bodies remain
in piped records. Without filters, the inbox and poll commands include every reservation
type. ``--line-id`` is an alias for ``--reservation-id``: the public API identifies
rental lines by reservation ID. ``--line-number`` is an alias for ``--number``.
ID and number filters are mutually exclusive; either can be combined with
``--type renewable|nonrenewable|verification``. Filtering by ID does not also
restrict by phone number, so messages from other reservations on a reused number
are excluded.

``poll`` uses the SDK's ``sms.incoming`` and waits for the first new batch of SMS.
``--follow`` continues streaming and deduplicates message IDs across batches.
``--timeout`` applies to the entire polling session (default 60 seconds, -1 for
indefinite waiting); ``--interval`` controls the SDK polling interval (default
3 seconds). Ctrl+C stops polling with exit code 130. An empty timeout exits with
code 1. Polling does not purchase a number, cancel a verification or wake a rental.

Live polling starts at the current UTC time. Use ``--since`` to include earlier
messages; ISO 8601 timestamps without a timezone are interpreted as UTC. Inbox
defaults to five messages; ``--limit N`` overrides the cap. Bounded candidates
from the API are sorted by received time, newest first; cross-page ordering
remains the API's ordering. Both commands show tables in a terminal and tab-separated records when piped or
redirected. Tab-separated output preserves full fields without width wrapping;
bodies containing tabs or newlines are CSV-quoted. Piped polling emits no waiting
indicator; empty results and timeout notices go to stderr as plain text.
Records are flushed immediately for pipelines. SMS TSV columns are ``ID``,
``To``, ``From``, ``Code``, ``Body``, ``Received``. Received timestamps include
the local UTC offset. Terminal body previews flatten whitespace and truncate
to fit the table; pipe output preserves the full body. Polling retains every
incoming message, including all messages in a batch and across ``--follow``
batches. No raw JSON is shown.
``--mock`` selects server mock resources automatically. ``tv --mock poll``
defaults to ``mock_ver_success``; ``--type renewable`` and ``--type nonrenewable``
select ``mock_ren_30d`` and ``mock_nonren_30d``. The unfiltered mock inbox combines
all three scopes and deduplicates SMS IDs. Explicit ``mock_*`` IDs are preserved;
other IDs and phone numbers are overridden rather than querying real SMS.
Mock polling includes fixed messages from the Unix epoch by default, so no
``--since`` is needed. An explicit ``--since`` is still honored. Live polling
continues to yield only new messages.

.. code-block:: bash

   tv --mock inbox
   tv --mock poll
   tv --mock poll --type renewable
   tv --mock poll --line-id mock_ver_pending --timeout 10

Existing verifications and purchase recovery
--------------------------------------------

.. code-block:: bash

   tv verifications
   tv verifications list --limit 100
   tv verifications show VERIFICATION_ID
   tv verifications resume VERIFICATION_ID
   tv verifications cancel VERIFICATION_ID
   tv --mock verifications show
   tv --mock verifications resume
   tv verify gmail --area-code 415 --area-code 650 --carrier att
   tv rentals sale SALE_ID

``resume`` waits for an existing verification's code without buying another
number. ``cancel`` fetches current API eligibility and requires confirmation or
``--yes``. Verification ID arguments are optional with ``--mock``; other IDs
are overridden with a server mock ID, while explicit ``mock_*`` IDs are retained.
Mock listing reads mock verification details rather than real account history.
``--area-code`` and ``--carrier`` can be repeated for verification purchases;
the quote includes these selection options and its price is the purchase cap.

A successful purchase prints its verification or sale ID. If creation succeeds
but loading details fails, the CLI reports acceptance and provides a recovery
command. Use ``verifications show`` / ``resume`` or ``rentals sale`` to inspect
the existing purchase. ``rentals sale`` requires the actual returned sale ID in
both live and mock mode. A lost connection during creation can leave the outcome
unknown: inspect your account before retrying. Purchases are never automatically
retried. This tracking is scoped to CLI creation requests; SDK behavior is
unchanged.

Services, rental lists/details and verification lists/details also emit TSV when
redirected. Service columns are ``Service``, ``Capability``, ``Price`` (blank if
not quoted). Rental columns are ``ID``, ``Number``, ``Service``, ``Type``, ``State``,
``Created``. Verification columns are ``ID``, ``Number``, ``Service``, ``State``,
``Created``. Creation times are the final column and use the system's local
timezone (``TZ`` under Unix/WSL); piped timestamps include the UTC offset.
Interactive summaries omit IDs; use ``show`` or pipe the list for complete IDs.
The default verification list limit is five; ``list --limit N`` overrides it.
``tv services`` and ``tv rentals services`` also default to five results and
accept ``--limit N``. Catalog results are alphabetical and do not have timestamps
in the public API. A notice shows when more matching services are available;
with pipes, that notice goes to stderr. Pricing queries cover only displayed
verification services.
These are distinct from the six-column SMS format. Empty lists emit no records;
notices and failures go to stderr. Purchase and action commands retain plain
status lines. Terminal output retains tables and verification animations.


Rentals
-------

.. code-block:: bash

   tv rentals
   tv rentals list --kind renewable --limit 100
   tv rentals services gmail --kind nonrenewable
   tv rentals price gmail --kind nonrenewable --duration sevenDay
   tv rentals buy gmail --kind nonrenewable --duration sevenDay
   tv rentals buy gmail --always-on --area-code 415 --area-code 650
   tv rentals services gmail --number-type voip
   tv rentals price gmail --number-type voip
   tv rentals buy gmail --number-type voip
   tv rentals show RENTAL_ID
   tv rentals notes RENTAL_ID
   tv rentals health RENTAL_ID
   tv rentals wake RENTAL_ID --wait
   tv rentals backorder BACKORDER_ID
   tv rentals renew OVERDUE_RENEWABLE_ID
   tv rentals extend NONRENEWABLE_ID --duration sevenDay
   tv rentals reactivate EXPIRED_ID
   tv rentals refund RENTAL_ID
   tv rentals update RENTAL_ID --notes "work line" --tags work
   tv rentals update RENEWABLE_ID --no-renewal
   tv rentals update RENTAL_ID --tags --mark-read

``rentals`` defaults to five entries total across both rental types, with the
most recent fetched creation times first. ``list --limit N`` changes the total
limit; ``--kind`` restricts the feed to one rental type. The two feeds are fetched
concurrently after authentication, reading at most ``offset + N`` entries from each instead
of scanning the entire account. Ordering across pages remains the API's ordering;
the CLI sorts these bounded candidates by creation time. ``show`` retains
always-on, expiry and renewal details outside the summary table.
The rental service catalog uses the requested reservation type. ``price`` and
``buy`` default to renewable, 30-day mobile SMS rentals; duration choices are the
SDK's generated ``RentalDuration`` values, visible in command help.
Rental ``services``, ``price`` and ``buy`` accept ``--number-type`` with the
SDK's generated number types (mobile by default). The catalog, quote and creation
request use the same selected type.
``--always-on`` requests a line that receives SMS without waking. Otherwise use
``wake``; ``--wait`` waits through the SDK until the scheduled usage window opens.

Purchases show the API quote and require confirmation or ``--yes``. Optional
``--billing-cycle`` assigns a renewable rental to an existing cycle, and
``--backorder`` permits a backorder when stock is unavailable. Purchases follow the
SDK sale and reservation links, displaying assigned lines and backorder IDs. The
rental create API has no price-cap field; reactivation supports a cap and uses the
quoted reactivation cost.

``renew`` applies to overdue renewable rentals. ``extend`` applies to
nonrenewable rentals. These actions, reactivation and refunds require confirmation
or ``--yes``. ``update`` changes only specified fields; tags replace existing tags,
and ``--tags`` with no values clears them. Renewal preferences apply only to
renewable rentals.

``--mock`` uses the SDK mock scenario for rental quotes and purchases. Listing
reads the server's renewable and nonrenewable mock rental details. ID-based commands
preserve explicit ``mock_*`` IDs, and otherwise choose the matching server mock
resource automatically. IDs may be omitted with ``--mock``. ``--kind`` selects the
rental type (renewable by default; ``extend`` defaults to nonrenewable).
Reactivation and overdue renewal select expired mock resources, and backorder
commands select ``mock_bo_success``.

.. code-block:: bash

   tv --mock rentals
   tv --mock rentals show --kind nonrenewable
   tv --mock rentals reactivate --yes
   tv --mock rentals backorder

The SDK and public API do not supply mock responses for every endpoint.
Authentication, accounts and the service catalog retain their normal SDK behavior.
Endpoints without server mock support return API errors even with a mock ID;
the CLI preserves that behavior without a local fake backend or fallback to real
rental IDs. Mock action responses are not persisted by the API.


Architecture and generation
---------------------------

.. code-block:: text

   textverified/terminal/
     __init__.py       optional entry point, package version
     __main__.py       module launcher
     cli.py            shared UI, account and verification commands
     messages.py       unified SMS inbox and SDK incoming polling
     rentals.py        rental catalog, purchases and management
     verifications.py  existing verification management and resume
     credentials.py    environment pair and atomic credential cache
     brand.py          colors and Unicode animation
     logo_data.py      logo pixel masks

Commands call existing SDK account, service, pricing, verification and SMS
APIs directly, using generated enums/dataclasses (including ``Reservation`` for exact-ID
SMS queries). Endpoint modules, ``PaginatedList`` and ``generate_enums.py`` are
unchanged. There is no second schema catalog, serializer or UI generator.
Timeouts and disabled purchase retries are scoped to the terminal client.

The existing ``swagger.json`` -> ``generate_enums.py`` pipeline generates SDK
types and ``tests/mock_endpoints_generated``. Terminal integration tests reuse
those fixtures through the existing HTTP mock loader. For an API schema change:

.. code-block:: bash

   pip install -e ".[dev,tui,docs]"
   python generate_enums.py
   python -m pytest tests/test_terminal.py tests/test_terminal_operations.py
   python -m pytest

Review the normal generated SDK diff. No terminal generation or asset rebuild
is needed. Changed SDK signatures are caught by request-shape tests and the
mocked end-to-end verification flow. Package version comes from
``textverified/_version.py``. Terminal requests use
``TextVerified-Python-TUI/<__version__>``; SDK defaults use the same package
version, with custom user agents preserved.

Functionality checks
--------------------

``python -m pytest tests/test_terminal.py tests/test_terminal_operations.py`` exercises live and mock verification, service
selection, spending confirmation, cancellation paths, credential persistence,
Unicode animation, interactive result rendering and the real SDK flow through
existing generated HTTP fixtures. Tests do not use real credentials or spend
credits. To try the app manually:

.. code-block:: bash

   tv login
   tv services discord
   tv --mock verify discord --yes
   tv --mock --no-animation verify discord --yes

Omit ``--yes`` to exercise confirmation. Ctrl+C during the waiting card exercises
cancellation. Mock API connectivity and terminal clipboard acceptance require
manual checks; automated tests use generated HTTP fixtures and no network.
