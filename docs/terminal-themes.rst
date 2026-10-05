Themes and terminal customization
=================================

The default ``textverified-dark`` theme uses blue accents on navy surfaces,
with clear table headers, alternating rows and a blue selection highlight.
``textverified-light`` provides blue accents on light surfaces. No special font
is required. The optional ``terminal`` theme inherits the ANSI palette; choose
terminal polarity dark/light explicitly when auto detection is unavailable.
NO_COLOR requests monochrome output. ``--reset-style`` restores the terminal
palette as a recovery option.

.. code-block:: bash

   textverified theme list
   textverified theme set terminal
   textverified theme set textverified-dark
   textverified theme set textverified-light
   textverified tui --theme terminal --reset-style

Ctrl+P exposes theme actions for immediate preview and validated persistence.
Config path identifies the themes directory. Add a local TOML file:

.. code-block:: toml

   schema_version = 1
   name = "my-terminal"
   base = "terminal"
   polarity = "dark"

   [colors]
   background = "default"
   foreground = "default"
   accent = "ansi_cyan"
   border = "ansi_bright_black"
   warning = "ansi_yellow"
   error = "ansi_red"

   [styles]
   selection = "reverse bold"

Save as themes/my-terminal.toml, then ``theme set custom:my-terminal``.
Accepted colors are default, ANSI color names (including bright variants), and
#RRGGBB. Accepted styles are reverse, bold, underline, normal and italic. Theme
files are data; no Python, shell hooks or remote downloads are executed.

Semantic color tokens map to Textual theme variables in terminal/themes.py:
background, foreground, surface, muted, accent, border, focus, selection_background,
selection_foreground, success, warning, error, unread, header_background,
header_foreground, footer_background and footer_foreground. Selection style maps
to block-cursor-text-style. Themes cannot change purchase confirmation logic.

Optional TCSS
-------------

Set appearance.style_file to a local path relative to the configuration directory.
The override loads after bundled app.tcss. Stable selectors are #account-bar,
#controls, #clock, #purchase-strip, #numbers-list, #inbox-list, #details,
#purchase-modal and #purchase-review. DataTable > .datatable--cursor identifies
selected-row styling. Example:

.. code-block:: css

   #account-bar { text-style: bold; }
   #details { border-top: solid $accent; }

Invalid themes/styles fall back to the bundled terminal presentation with a
visible diagnostic. ``tui --reset-style`` skips overrides; ``theme set terminal``
resets the saved theme. Palette contrast and actual terminal clipboard support
must be checked in the target terminal; see :doc:`terminal-testing`.
