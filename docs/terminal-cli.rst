CLI reference
=============

Generated with ``python generate_terminal_docs.py`` from implemented help.
Root options precede subcommands. Static shell completion needs no credentials:
``textverified --install-completion`` or ``textverified --show-completion``.

textverified
------------

.. code-block:: text

   Usage: textverified [OPTIONS] COMMAND [ARGS]...

    TextVerified numbers and account-wide SMS. Install: pip install textverified

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --profile                                       <str>                                           │
   │ --non-interactive       --no-non-interactive           [default: no-non-interactive]            │
   │ --color                                         <str>  [default: auto]                          │
   │ --debug                 --no-debug                     [default: no-debug]                      │
   │ --version                                                                                       │
   │ --install-completion                                   Install completion for the current       │
   │                                                        shell.                                   │
   │ --show-completion                                      Show completion for the current shell,   │
   │                                                        to copy it or customize the              │
   │                                                        installation.                            │
   │ --help                                                 Show this message and exit.              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Commands ──────────────────────────────────────────────────────────────────────────────────────┐
   │ tui            Open the full-screen Numbers / Inbox application.                                │
   │ list                                                                                            │
   │ auth           Manage locally cached account credentials.                                       │
   │ account                                                                                         │
   │ verification                                                                                    │
   │ rental                                                                                          │
   │ sms                                                                                             │
   │ schema                                                                                          │
   │ theme                                                                                           │
   │ config                                                                                          │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified tui
----------------

.. code-block:: text

   Usage: textverified tui [OPTIONS]

    Open the full-screen Numbers / Inbox application.

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --theme                              <str>                                                      │
   │ --reset-style    --no-reset-style           [default: no-reset-style]                           │
   │ --help                                      Show this message and exit.                         │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified auth
-----------------

.. code-block:: text

   Usage: textverified auth [OPTIONS] COMMAND [ARGS]...

    Manage locally cached account credentials.

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Commands ──────────────────────────────────────────────────────────────────────────────────────┐
   │ login    Ask for Email and API key, validate and save in the local cache.                       │
   │ logout                                                                                          │
   │ status                                                                                          │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified auth login
-----------------------

.. code-block:: text

   Usage: textverified auth login [OPTIONS]

    Ask for Email and API key, validate and save in the local cache.

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --profile        <str>  [default: default]                                                      │
   │ --help                  Show this message and exit.                                             │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified auth status
------------------------

.. code-block:: text

   Usage: textverified auth status [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified auth logout
------------------------

.. code-block:: text

   Usage: textverified auth logout [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --profile        <str>  [default: default]                                                      │
   │ --help                  Show this message and exit.                                             │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified account show
-------------------------

.. code-block:: text

   Usage: textverified account show [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --format        <str>  [default: table]                                                         │
   │ --json                                                                                          │
   │ --help                 Show this message and exit.                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified list
-----------------

.. code-block:: text

   Usage: textverified list [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --limit         <int>                                                                           │
   │ --all                                                                                           │
   │ --query         <str>                                                                           │
   │ --format        <str>  [default: table]                                                         │
   │ --json                                                                                          │
   │ --state         <str>  [default: all]                                                           │
   │ --kind          <str>  [default: all]                                                           │
   │ --help                 Show this message and exit.                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified verification list
------------------------------

.. code-block:: text

   Usage: textverified verification list [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --limit         <int>                                                                           │
   │ --all                                                                                           │
   │ --query         <str>                                                                           │
   │ --format        <str>  [default: table]                                                         │
   │ --json                                                                                          │
   │ --state         <str>  [default: all]                                                           │
   │ --kind          <str>  [default: all]                                                           │
   │ --help                 Show this message and exit.                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified verification get
-----------------------------

.. code-block:: text

   Usage: textverified verification get [OPTIONS] {id}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    id      <str>  [required]                                                                  │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --json                                                                                          │
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified verification quote
-------------------------------

.. code-block:: text

   Usage: textverified verification quote [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --service                                                    <str>                              │
   │ --capability                                                 <str>                              │
   │ --area-code                                                  <str>                              │
   │ --carrier                                                    <str>                              │
   │ --max-price                                                  <str>                              │
   │ --require-server-price-cap    --no-require-server-price-…           [default:                   │
   │                                                                     no-require-server-price-ca… │
   │ --yes                         --no-yes                              [default: no-yes]           │
   │ --set                                                        <str>                              │
   │ --set-json                                                   <str>                              │
   │ --input-json                                                 <str>                              │
   │ --format                                                     <str>  [default: table]            │
   │ --json                                                                                          │
   │ --help                                                              Show this message and exit. │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified verification buy
-----------------------------

.. code-block:: text

   Usage: textverified verification buy [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --service                                                    <str>                              │
   │ --capability                                                 <str>                              │
   │ --area-code                                                  <str>                              │
   │ --carrier                                                    <str>                              │
   │ --max-price                                                  <str>                              │
   │ --require-server-price-cap    --no-require-server-price-…           [default:                   │
   │                                                                     no-require-server-price-ca… │
   │ --yes                         --no-yes                              [default: no-yes]           │
   │ --set                                                        <str>                              │
   │ --set-json                                                   <str>                              │
   │ --input-json                                                 <str>                              │
   │ --format                                                     <str>  [default: table]            │
   │ --json                                                                                          │
   │ --help                                                              Show this message and exit. │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified verification cancel
--------------------------------

.. code-block:: text

   Usage: textverified verification cancel
               [OPTIONS] {id}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    id      <str>  [required]                                                                  │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --yes     --no-yes      [default: no-yes]                                                       │
   │ --help                  Show this message and exit.                                             │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified rental list
------------------------

.. code-block:: text

   Usage: textverified rental list [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --limit         <int>                                                                           │
   │ --all                                                                                           │
   │ --query         <str>                                                                           │
   │ --format        <str>  [default: table]                                                         │
   │ --json                                                                                          │
   │ --state         <str>  [default: all]                                                           │
   │ --kind          <str>  [default: all]                                                           │
   │ --help                 Show this message and exit.                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified rental get
-----------------------

.. code-block:: text

   Usage: textverified rental get [OPTIONS] {id}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    id      <str>  [required]                                                                  │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --json                                                                                          │
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified rental quote
-------------------------

.. code-block:: text

   Usage: textverified rental quote [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --service                                                    <str>                              │
   │ --capability                                                 <str>                              │
   │ --duration                                                   <str>                              │
   │ --renewable                   --no-renewable                                                    │
   │ --always-on                   --wakeable                                                        │
   │ --area-code                                                  <str>                              │
   │ --max-price                                                  <str>                              │
   │ --require-server-price-cap    --no-require-server-price-…           [default:                   │
   │                                                                     no-require-server-price-ca… │
   │ --yes                         --no-yes                              [default: no-yes]           │
   │ --set                                                        <str>                              │
   │ --set-json                                                   <str>                              │
   │ --input-json                                                 <str>                              │
   │ --format                                                     <str>  [default: table]            │
   │ --json                                                                                          │
   │ --help                                                              Show this message and exit. │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified rental buy
-----------------------

.. code-block:: text

   Usage: textverified rental buy [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --service                                                    <str>                              │
   │ --capability                                                 <str>                              │
   │ --duration                                                   <str>                              │
   │ --renewable                   --no-renewable                                                    │
   │ --always-on                   --wakeable                                                        │
   │ --area-code                                                  <str>                              │
   │ --max-price                                                  <str>                              │
   │ --require-server-price-cap    --no-require-server-price-…           [default:                   │
   │                                                                     no-require-server-price-ca… │
   │ --yes                         --no-yes                              [default: no-yes]           │
   │ --set                                                        <str>                              │
   │ --set-json                                                   <str>                              │
   │ --input-json                                                 <str>                              │
   │ --format                                                     <str>  [default: table]            │
   │ --json                                                                                          │
   │ --help                                                              Show this message and exit. │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified rental wake
------------------------

.. code-block:: text

   Usage: textverified rental wake [OPTIONS] {id}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    id      <str>  [required]                                                                  │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --yes     --no-yes      [default: no-yes]                                                       │
   │ --help                  Show this message and exit.                                             │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified sms list
---------------------

.. code-block:: text

   Usage: textverified sms list [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --limit         <int>                                                                           │
   │ --all                                                                                           │
   │ --query         <str>                                                                           │
   │ --format        <str>  [default: table]                                                         │
   │ --json                                                                                          │
   │ --number        <str>                                                                           │
   │ --type          <str>  [default: all]                                                           │
   │ --since         <str>                                                                           │
   │ --before        <str>                                                                           │
   │ --id            <str>                                                                           │
   │ --kind          <str>                                                                           │
   │ --help                 Show this message and exit.                                              │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified sms watch
----------------------

.. code-block:: text

   Usage: textverified sms watch [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --number         <str>                                                                          │
   │ --type           <str>    [default: all]                                                        │
   │ --since          <str>                                                                          │
   │ --before         <str>                                                                          │
   │ --id             <str>                                                                          │
   │ --kind           <str>                                                                          │
   │ --query          <str>                                                                          │
   │ --tail           <int>                                                                          │
   │ --resume         <str>                                                                          │
   │ --timeout        <float>  [default: 0]                                                          │
   │ --format         <str>    [default: table]                                                      │
   │ --json                                                                                          │
   │ --help                    Show this message and exit.                                           │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified sms wait
---------------------

.. code-block:: text

   Usage: textverified sms wait [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --number                         <str>                                                          │
   │ --type                           <str>    [default: all]                                        │
   │ --since                          <str>                                                          │
   │ --id                             <str>                                                          │
   │ --kind                           <str>                                                          │
   │ --query                          <str>                                                          │
   │ --timeout                        <float>  [default: 120]                                        │
   │ --code-only    --no-code-only             [default: no-code-only]                               │
   │ --json                                                                                          │
   │ --help                                    Show this message and exit.                           │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified schema show
------------------------

.. code-block:: text

   Usage: textverified schema show [OPTIONS] {operation}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    operation      <str>  [required]                                                           │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified theme list
-----------------------

.. code-block:: text

   Usage: textverified theme list [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified theme set
----------------------

.. code-block:: text

   Usage: textverified theme set [OPTIONS] {name}

   ┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────┐
   │ *    name      <str>  [required]                                                                │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified config path
------------------------

.. code-block:: text

   Usage: textverified config path [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified config show
------------------------

.. code-block:: text

   Usage: textverified config show [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘

textverified config validate
----------------------------

.. code-block:: text

   Usage: textverified config validate [OPTIONS]

   ┌─ Options ───────────────────────────────────────────────────────────────────────────────────────┐
   │ --help          Show this message and exit.                                                     │
   └─────────────────────────────────────────────────────────────────────────────────────────────────┘
