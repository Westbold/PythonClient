Machine output and process behavior
===================================

Finite lists default to table; --json aliases --format json. --format ndjson
exports one complete event per line, flushed immediately. Watch accepts table
or ndjson; --json is rejected because it would imply a finite array. Results go
to stdout, diagnostics to stderr. JSON has no ANSI decoration and uses snake_case
keys, schema_version 1, UTC RFC 3339 timestamps, string phone numbers/codes and
string amounts. Missing data is null. Additive fields are compatible; changed
meaning/types or removed keys require a new schema version.

Example finite list (empty successful account):

.. code-block:: json

   {"schema_version":1,"account":{"profile":null,"username":"example","api_origin":"https://www.textverified.com"},"items":[],"meta":{"scope":"account","history_scope":"api_available","requested_limit":100,"returned":0,"scan_complete":true,"has_more":false,"fetched_at":"2026-10-01T00:00:00Z","snapshot_consistency":"best_effort","warnings":[]}}

Lists default to 100 matching records. --limit limits matches, not scanned rows;
--all scans API-available history and conflicts with an explicit --limit. A bounded
result can report scan_complete false and has_more true. JSON is privately spooled
before stdout is committed, so failed finite scans do not leave half a document.
NDJSON may emit valid earlier lines before a later error.

SMS contains id, created_at, observed_at, to_number, from_number, body, parsed_code,
content_state, resource_kind, resource_id, service and association_source.
Unfiltered association is unknown because the pinned SMS shape contains no IDs;
--id together with --kind uses the documented scoped query and labels provenance
scoped_query. --number is explicitly a broader phone scope. since is inclusive,
before exclusive; naive timestamps are rejected. Time filters exclude messages
with unknown timestamps, disclosed in finite list warnings.

Example stream event:

.. code-block:: json

   {"schema_version":1,"event":"sms.received","replay":false,"account":{"profile":null,"username":"example","api_origin":"https://www.textverified.com"},"observed_at":"2026-10-01T00:00:01Z","message":{"id":"m1","created_at":"2026-10-01T00:00:00Z","observed_at":"2026-10-01T00:00:01Z","to_number":"001234","from_number":"12345","body":"Your code","parsed_code":"001234","content_state":"available","resource_kind":"unknown","resource_id":null,"service":null,"association_source":"unknown"}}

Watch emits sms.received for new identities and sms.updated for material body/code
changes. Different IDs with identical bodies are retained. Finite SMS exports use
sms.received with replay true; resources use resource.snapshot with a resource key.
Watch defaults to a 20-message tail, emitted oldest to newest, then live events.
--tail 0 silently establishes a full baseline first. --since replays matching
history before live observations. --resume NAME binds a checkpoint to account and
filters, and conflicts with explicit tail/since. Checkpoints follow flushed
output; replay after a crash is possible. Consumers deduplicate by account/message
ID and apply updates. Delivery is at least once across restarts, not exactly once.

Wait normally establishes a silent baseline. --since permits historical matches,
choosing earliest timestamp/ID. --code-only waits for a nonempty server code and
prints just that code plus newline, preserving leading zeroes. It never extracts
a code heuristically. Default wait timeout is 120 seconds; zero means unlimited.
Watch --timeout is a successful duration limit; wait timeout is exit 8 with empty
stdout. Both use monotonic elapsed time. Neither wakes or buys a number.

Exit statuses
-------------

0 success; 1 unexpected internal error; 2 invalid usage/configuration/confirmation;
3 authentication/authorization; 4 not found; 5 known API/business rejection;
6 network/rate-limit exhaustion; 7 unsupported capability/price protection;
8 wait timeout; 9 mutation outcome unknown; 130 interrupt. An accepted purchase
with pending details returns 0 with outcome accepted. Broken pipes close cleanly.

Machine-mode diagnostics are single-line JSON on stderr:

.. code-block:: json

   {"schema_version":1,"error":{"code":"purchase_outcome_unknown","message":"Inspect account and operation receipt before retrying","retryable":false}}

No headers, keys, bearer tokens, raw server bodies or SMS content appear in error
diagnostics. Progress uses a status object on stderr, never an SMS stdout event.
