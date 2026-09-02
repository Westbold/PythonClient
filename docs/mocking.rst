Server Test Modes
=================

The Phoneblur API provides server-backed ``test_*`` scenarios. They never
deduct balance or create real resources. The client exposes those scenarios as
``TestMode`` enum values and sends their documented service name only for the
operations that accept ``service_name``.

The base mode is ``LIVE``: ``textverified.test_mode`` is
``TestMode.LIVE`` by default. ``test=None`` inherits the client or global
mode; use ``LIVE`` explicitly to force ordinary API behavior.

Configuration Scopes
--------------------

Set a global mode for clients that inherit the package setting:

.. code-block:: python

   import textverified
   from textverified import MOCK_SUCCESS

   textverified.test_mode = MOCK_SUCCESS
   # Equivalent: textverified.set_test_mode(MOCK_SUCCESS)

Set a mode for one client:

.. code-block:: python

   from textverified import TextVerified, MOCK_PENDING

   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username",
       test_mode=MOCK_PENDING,
   )

Every service-name operation accepts a per-call ``test`` override:

.. code-block:: python

   from textverified import MOCK_NO_NUMBERS, NumberType, ReservationCapability

   client.services.verification_inventory(
       number_type=NumberType.MOBILE,
       service_name="any-real-service-name",
       capability=ReservationCapability.SMS,
       test=MOCK_NO_NUMBERS,
   )

The order of precedence is per-call ``test``, per-client ``test_mode``, then
global ``textverified.test_mode``. ``test=None`` (including the default)
inherits that setting. Use ``test=LIVE`` to make one call live even when a
parent scope selects a test scenario.

Supported Operations
--------------------

The ``test`` argument is available on all operations that submit a service
name:

* ``verifications.create`` and ``verifications.pricing``
* ``reservations.create`` and ``reservations.pricing``
* ``services.verification_inventory`` and ``services.rental_inventory``

The API identifies test responses with the ``X-Phoneblur-Mock: true``
*response* header. The client does not send that header; it activates a test
scenario by replacing the request's ``serviceName`` with the selected enum's
server value.

Available TestMode Values
-------------------------

The enum values below correspond directly to Phoneblur's documented server
scenarios. They are also available as module-level names, such as
``textverified.MOCK_SUCCESS``.

* ``LIVE`` — normal API behavior; this is the default.
* ``MOCK_SUCCESS`` — successful verification or active rental.
* ``MOCK_DELAYED_SUCCESS`` and ``MOCK_PENDING`` — verification polling flows.
* ``MOCK_TIMEOUT`` and ``MOCK_REACTIVATABLE`` — verification terminal states.
* ``MOCK_RENEWABLE_EXPIRED`` and ``MOCK_NONRENEWABLE_EXPIRED`` — expired rentals.
* ``MOCK_BACKORDER`` — rental backorder; requires
  ``allow_back_order_reservations=True``.
* ``MOCK_INSUFFICIENT_BALANCE`` — API error ``InsufficientBalance``.
* ``MOCK_NO_NUMBERS`` — API error ``Unavailable``.
* ``MOCK_TOO_MANY_UNFINISHED_VERIFICATIONS`` — API error
  ``TooManyUnfinishedVerifications``.

The verification-only scenarios are ``MOCK_DELAYED_SUCCESS``, ``MOCK_PENDING``,
``MOCK_TIMEOUT``, ``MOCK_REACTIVATABLE``, and
``MOCK_TOO_MANY_UNFINISHED_VERIFICATIONS``. The rental-only scenarios are
``MOCK_RENEWABLE_EXPIRED``, ``MOCK_NONRENEWABLE_EXPIRED``, and
``MOCK_BACKORDER``. ``MOCK_SUCCESS``, ``MOCK_INSUFFICIENT_BALANCE``, and
``MOCK_NO_NUMBERS`` work for both kinds of reservation.

Failure Example
---------------

.. code-block:: python

   from textverified import (
       MOCK_INSUFFICIENT_BALANCE,
       ReservationCapability,
       TextVerified,
   )

   client = TextVerified(api_key="your_api_key", api_username="your_username")

   # The server returns its normal 400 InsufficientBalance response.
   client.verifications.create(
       service_name="any-real-service-name",
       capability=ReservationCapability.SMS,
       test=MOCK_INSUFFICIENT_BALANCE,
   )
