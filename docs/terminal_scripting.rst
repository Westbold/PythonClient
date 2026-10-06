Piping and automation
=========================

Install the optional app with ``pip install "textverified[tui]"`` and run
``tv login`` first. ``textverified`` can replace ``tv`` in every example.
The shell examples below use Bash unless marked otherwise.
Inbox snapshots default to five recent messages; pass ``--limit N`` for larger
archives. Polling streams every incoming message without this snapshot cap.
Every ``--limit`` command supports ``--offset`` as well; for example,
``tv inbox --offset 5 --limit 5`` skips the first five matching messages.
Use time filters and message IDs when resuming a changing feed, since new
messages can shift numeric offsets between snapshots.

Record format
-----------------

When stdout is a pipe or file, ``inbox`` and ``poll`` emit tab-separated records
with these columns, in order:

.. code-block:: text

   ID    To    From    Code    Body    Received

The separators are literal tabs. Each batch starts with this header, including
each batch from ``poll --follow``. Empty results produce no header or records.
Fields remain strings: phone numbers and codes can have leading zeroes. Received
times are the final column and use ISO 8601 in the local timezone, including
the UTC offset. Bodies retain their full text; tabs, newlines and quotation
marks are escaped using CSV quoting. An encrypted body without readable content
is displayed as ``[encrypted]``.

Use a CSV reader with a tab delimiter. ``cut``, ``awk`` and reading one physical
line at a time can split quoted SMS bodies incorrectly. Colors, animations and
cursor controls are absent from redirected output, even with ``--color=always``.
Empty-result and timeout notices go to stderr, leaving stdout for records.

Archive an inbox snapshot
-----------------------------

.. code-block:: bash

   tv inbox --line-id "$RENTAL_ID" --type renewable --limit 500 \
     > inbox.tsv 2> inbox.log

Set ``RENTAL_ID`` to your rental's reservation ID. This retrieves up to 500
messages, following SDK pagination. Use ``--since 2026-10-05T00:00:00Z`` to
restrict the time range. Keeping stderr separate prevents notices from becoming
data rows. An empty inbox succeeds with an empty output file. Check the command's
exit status before importing the file: API and authentication failures exit 1
and print plain errors to stderr. A failure after earlier batches can leave a
partial data file.

Parse snapshots and streams safely
--------------------------------------

Save the following as ``consume_sms.py``. It accepts snapshots or continuous
polling, skips repeated batch headers and converts each message to one JSON line.
With ``--codes``, it emits only nonempty verification codes. Quoted multiline
bodies are read as a single record; JSON escapes their newlines.

.. code-block:: python

   import argparse
   import csv
   import json
   import sys

   parser = argparse.ArgumentParser()
   parser.add_argument("--codes", action="store_true")
   args = parser.parse_args()
   header = ["ID", "To", "From", "Code", "Body", "Received"]

   for row in csv.reader(sys.stdin, delimiter="\t"):
       if not row or row == header:
           continue
       if len(row) != len(header):
           raise SystemExit("Invalid SMS record: expected six columns")
       message = dict(zip(header, row))
       if args.codes:
           if message["Code"]:
               print(message["Code"], flush=True)
       else:
           print(json.dumps(message, ensure_ascii=True), flush=True)

.. code-block:: bash

   python consume_sms.py < inbox.tsv > inbox.jsonl
   tv --mock inbox | python -u consume_sms.py --codes
   tv --mock poll --follow --timeout 10 --interval 1 \
     | python -u consume_sms.py

The last two pipelines also work in PowerShell when written on one line.
``--mock`` uses server-backed mock SMS and requires credentials and network
access. Mock messages have fixed IDs; follow mode emits each ID once per polling
session, so it does not generate an endless stream of new test messages.

Stream a rental into a downstream process
---------------------------------------------

.. code-block:: bash

   set -o pipefail
   tv poll --line-id "$RENTAL_ID" --type renewable --follow --timeout -1 \
     2> poll.log | python -u consume_sms.py | tee -a messages.jsonl

The CLI flushes each batch immediately. ``python -u`` and the consumer's
``flush=True`` keep downstream output moving as messages arrive. ``tee -a``
appends the converted records to a file while displaying them. Receiving rental
SMS requires an always-on or awake line; polling itself does not wake it.

Live polling starts at the current UTC time. To resume from an earlier time, pass
``--since`` with your saved timestamp. Deduplication is limited to the current
CLI polling session. A durable consumer should track ``ID`` across restarts,
especially when resuming with an overlapping time range. Appending raw TSV also
appends batch headers; the reader above handles these repeated headers.

Handle timeouts and failures
--------------------------------

.. code-block:: bash

   set -o pipefail
   if tv poll --line-id "$RENTAL_ID" --type renewable --timeout 30 \
       2> poll.log | tee poll.tsv | python -u consume_sms.py --codes > codes.txt; then
     printf 'Polling completed; codes saved to codes.txt\n'
   else
     printf 'Polling or parsing failed; inspect poll.tsv, poll.log and stderr\n' >&2
   fi

Without ``pipefail``, Bash reports only the last pipeline command's status, so a
successful consumer could hide a failed poll. Poll exits 0 if it received SMS,
even when those messages contain no parsed code. It exits 1 when the timeout
expires without new SMS; API and other command errors can also exit 1, so inspect
stderr rather than treating every failure as an empty timeout. ``tee poll.tsv``
preserves the received records for inspection. Ctrl+C exits 130.
A failure after earlier batches may leave partial output; a consumer should not
assume a nonzero exit means that nothing was received.

Capture a purchased verification's code
-------------------------------------------

Verification output differs from inbox records: redirected ``verify`` prints
plain status lines and ends with the bare code on success. Check the command's
status before extracting that final line:

.. code-block:: bash

   if result=$(tv --mock verify gmail --yes); then
     code=$(printf '%s\n' "$result" | tail -n 1)
     printf 'Verification code: %s\n' "$code"
   else
     printf '%s\n' "$result" >&2
     printf 'Verification failed\n' >&2
   fi

``--yes`` answers the purchase confirmation for unattended scripts. This example
uses a mock verification; removing ``--mock`` purchases a real verification and
spends credits. Keep the code as a string to preserve leading zeroes.
