Terminal maintenance
====================

Install developer/terminal/documentation dependencies:

.. code-block:: bash

   pip install -e ".[dev,tui,docs]"
   python generate_terminal_metadata.py
   python generate_terminal_docs.py
   python -m pytest
   python -m sphinx -b html docs docs/_build/html

The package version lives in ``textverified/_version.py`` as ``__version__``.
Build metadata, Sphinx release information, release tags and CLI --version use
that value. SDK requests default to ``TextVerified-Python-Client/<version>``;
the terminal adapter uses ``TextVerified-Python-TUI/<version>``. Authentication
requests inherit the same agent through the SDK session defaults. Explicit SDK
user-agent overrides and TEXTVERIFIED_USER_AGENT for the static client remain
supported.

SDK generation remains unchanged. ``swagger.json`` is the pinned API input.
``generate_terminal_metadata.py`` generates only ``terminal/fields.json`` and
reuses the existing generator's field-name conversion. The metadata manifest includes the canonical JSON SHA-256 (sorted keys, compact separators, UTF-8),
API version and generator version. Writable descriptors include aliases,
required/default distinctions, descriptions, enums and nested validation shapes.
The terminal adapter preserves unknown raw lifecycle values; request enum
validation remains strict. SDK response types retain their existing behavior. Do not hand-edit generated dtypes or field metadata.

verification.buy and rental.buy are handwritten workflow mappings. Common flags
and form controls are curated; remaining writable fields are available through
Advanced JSON, --set, --set-json and --input-json. Python snake_case and API wire
aliases are accepted. Explicit duplicate assignments are rejected. Optional
omission, null, false, zero and empty values retain distinct wire representations.
ValidatedRequest sends its complete serialized payload through the terminal
adapter using the existing SDK transport. Adapter submit()/resolve() separate
purchase acceptance from detail retrieval without extending the SDK API.

For a schema change, review the generated descriptor diff, verify common aliases
and duration values still exist, update quote mappings when price-affecting
semantics change, and run field-to-mock-transport contracts. New required fields
must be collected through the form or Advanced JSON before shipping. Update
api-compatibility.md with the new hash and backend guarantees; type regeneration
does not establish deployed behavior. Never infer a price guarantee or SMS
association from a sample response.

The shared adapter owns SDK integration. CLI and TUI use Application/Feed and
never call each other or duplicate endpoint URLs. Blocking calls run off the
Textual event loop; one per-account lock serializes requests, released between
pages. Context generation guards reject old-account UI results. Bodies have a
bounded working set; identity metadata is kept separately. History/replay/export
streams inspect all available pages, with private temporary spooling where needed.
No background process survives the application.

Integration tests must opt into an explicitly supported nonproduction scenario.
Creation/pricing/inventory test modes do not authorize cancel/wake tests. Default
CI uses fake accounts, recorded transport requests and headless Textual tests.
