TextVerified Python Client
==========================

Python wrapper for the TextVerified API.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   mocking
   terminal
   terminal-cli
   terminal-output
   terminal-themes
   terminal-maintenance
   terminal-testing
   api_reference
   examples

Installation
------------

.. code-block:: bash

   pip install textverified

For the optional full-screen terminal and CLI (Python 3.10+):

.. code-block:: bash

   pip install "textverified[tui]"

See :doc:`terminal` for authentication, commands and shortcuts.

Quick Start
-----------

.. code-block:: python

   from textverified import TextVerified
   
   client = TextVerified(api_key="your_key", api_username="your_username")
   services = client.services.list()

API Reference
-------------

.. automodule:: textverified
   :members:
   :undoc-members:
   :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
