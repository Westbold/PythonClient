Terminal verification report
============================

Implementation verification uses Windows, Python 3.13.5, Textual 6.2.1 and Typer
0.27.2. No production credentials were loaded and no credits were spent.
The original 161 SDK tests and 57 terminal tests pass (218 total) with the optional terminal installed. New tests
cover account-wide externally created/inactive/unassociated messages; retained
late arrivals; duplicate bodies with distinct IDs; material code updates; newest
body retention (including a 100,000-message scan with 100 retained bodies); accepted/details-pending and unknown purchase outcomes;
server-price-cap rejection; omission/null/false/zero/empty preservation; schema
field transport; multi-page/cyclic/cross-origin links; atomic finite JSON errors;
search match limits; watch silent baseline; wait leading zeroes and timeout;
whole-pair credential precedence; unknown state preservation; literal safe text;
editable-field shortcuts; stable selection; and one-dispatch confirmation.

Run ``python -m pytest`` for the current exact count. Terminal tests are skipped
when the optional frameworks are absent, keeping SDK-only development usable.
The terminal CI installs the optional extra before running these tests.

Acceptance coverage
-------------------

The automated suite exercises the core acceptance groups A01/A03/A04, A06,
A15/A16, A18, A22-A30, A31/A32/A34, A37-A40, A43/A45/A46 and A51. Additional
headless tests cover login, resize, stale quote rejection, malformed-record partial coverage, themes and account isolation. These are
behavioral checks, not evidence of live-server ordering or financial atomicity.
A42 requires schema-change review and regenerated transport tests; the generic
Advanced/CLI path is shared and does not hardcode optional request fields.

Release checks still requiring an external environment
------------------------------------------------------

Live deployed pagination consistency/retention, reused-number scoped filtering,
renewable billing/wake semantics, production rate limits, and supported server
mock scenarios need backend-owner or opt-in validation. See the
:download:`API compatibility record <api-compatibility.md>`.

Real terminal matrix: Windows Terminal/PowerShell, macOS Terminal, a Linux terminal,
SSH, tmux, dark/light/custom ANSI palettes, 60/80/120-column breakpoints,
monochrome mode, clipboard unavailable, suspend/resume and abrupt interruption.
Only headless Textual layouts are automatically exercised in this checkout;
physical terminal behavior is not claimed verified. Review terminal/theme
screenshots before a release advertised as satisfying the full supplied
acceptance matrix. The implementation should not be represented as having
passed server-dependent or physical-terminal acceptance checks that were not run.
