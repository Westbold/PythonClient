TextVerified Python Client
==========================

Python wrapper for the TextVerified API.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   mocking
   terminal
   terminal_scripting
   api_reference
   examples

Installation
------------

.. code-block:: bash

   pip install textverified

For the optional terminal app: ``pip install "textverified[tui]"``. See
:doc:`terminal` for server-backed mock and real-account usage.

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
