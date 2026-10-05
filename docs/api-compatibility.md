# Terminal API compatibility

SDK: source checkout at `c33e0ec9b04357f0f8812c624f6d1dc4174b5026`, package version `0.1.0a3`, with the uncommitted terminal additions. API: `swagger.json`, version `v2`, canonical JSON SHA-256 `3195b3a8a42c5a6960d8fc10863ff1ad34603b5d7eb916ce9e11c6f1109c5e1d`. Field generator version: `1`.

## Verified in the pinned contract and local SDK

- `GET /api/pub/v2/sms` accepts an unfiltered account-wide query. `to`, `reservationId` and `reservationType` are documented filters. Exact ID/type queries label association `scoped_query`; unfiltered SMS has no authoritative resource ID/type and remains unknown.
- Lists use `data`, `hasNext`, and `links.next` read actions. The terminal adapter's page iterator retain one raw page at a time. They reject missing, cyclic, cross-origin, and non-GET pagination links.
- SMS is described as latest SMS, but no stable total ordering, snapshot consistency, incremental cursor, insertion ordering or retention period is specified. Live clients therefore reconcile all accessible pages, identify messages by ID, and detect content updates and retained late arrivals. Server history loss remains a possible gap; no exactly-once or complete lifetime archive is promised.
- No active-state filter is relied upon. All three compact resource lists are scanned before active discovery is marked complete. Unknown raw states are preserved as attention records.
- Verification `endsAt` is the deadline. Rental `endsAt` is expiration when supplied. Renewable billing-cycle `nextAutoRenewAttempt` is used for the renewal date; no date is invented from duration.
- Account balance is documented in account credits. SDK amounts arrive as floats; terminal amounts use `Decimal(str(value))` and JSON strings, which cannot recover precision already lost upstream. Pricing currency/unit is not specified and is left null.
- Verification `maxPrice` explicitly rejects a reservation above the cap. Rental request schema has no cap: rental maximum price is a preflight comparison; requiring a server cap fails before submission.
- Purchase POST responses are follow-up links. Terminal adapter `submit()` / `resolve()` methods expose acceptance separately and send the complete validated request without rebuilding a fixed field subset. Accepted purchases with unavailable details are not repeated.
- No purchase idempotency key is documented for these two creation request schemas. Mutation requests are sent once, including disabling connection retries. Ambiguous submissions write a receipt and require reconciliation rather than automatic retry.
- Rental `alwaysOn` is deprecated in this schema and documented as always true. The TUI labels this contract and omits that deprecated request value. The advanced field interface retains its metadata. Existing SDK wake operations remain explicit; opening Inbox never calls them. Wake-window cost/readiness guarantees have not been established.
- Default terminal HTTP timeout is 15 seconds per request. GETs have three attempts; POSTs have one. Retry-After delays are honored, with longer waits handed back to the live scheduler. Bearer authentication is reused until its SDK expiration.

## Release verification still required

No production credentials were used and no server-side purchases were made during implementation. Retention, cross-page mutation consistency, deployed filter behavior for reused numbers, rate limits, and billing/wake semantics need backend-owner or opt-in server validation. Documented `test_*` creation/pricing/inventory scenarios are not a universal sandbox for cancel/wake operations. Ordinary CI uses fake adapters and recorded mock transports only.

The automated Windows/Python test report is in `terminal-testing.rst`. Real macOS/Linux terminals, SSH/tmux, terminal palette variations, and clipboard acceptance must be checked before claiming those environments verified.
