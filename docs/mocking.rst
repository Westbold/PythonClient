API Mocking
===========

The client can use Phoneblur's server-backed mock scenarios for integration and
development testing. Mock responses are deterministic, never deduct balance,
and never create real resources.

Enable Mocking
--------------

Mocking is disabled by default. Enable it with the package-level flag or its
helper function before making requests:

.. code-block:: python

   import textverified
   from textverified import TextVerified, NumberType, ReservationCapability

   textverified.mock_api = True
   # Equivalent: textverified.set_mock_api(True)

   client = TextVerified(api_key="your_api_key", api_username="your_username")
   verification = client.verifications.create(
       service_name="any-real-service-name",
       capability=ReservationCapability.SMS,
   )

   # The request used the mock ``test_success`` service. Follow-up calls use
   # the returned mock resource IDs and work like normal API calls.
   print(verification.id)
   print(verification.number)

   textverified.mock_api = False

You can instead enable mocks for one client without changing the global flag:

.. code-block:: python

   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username",
       mock_api=True,
   )

When enabled, the flag substitutes the API's ``test_success`` service name on
these POST endpoints:

* Verification and rental creation
* Verification and rental pricing
* Verification and rental inventory checks

All other requests are unchanged. In particular, services, account, and
follow-up requests use their normal routes. The API identifies mock responses
with the ``X-Phoneblur-Mock: true`` *response* header; the client deliberately
does not send that header because it does not activate mocking.

Rental Example
--------------

.. code-block:: python

   import textverified
   from textverified import (
       TextVerified,
       NumberType,
       RentalDuration,
       ReservationCapability,
   )

   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username",
       mock_api=True,
   )

   sale = client.reservations.create(
       service_name="any-service",
       number_type=NumberType.MOBILE,
       capability=ReservationCapability.SMS,
       is_renewable=True,
       duration=RentalDuration.THIRTY_DAY,
       always_on=True,
       allow_back_order_reservations=False,
   )
   print(sale.id)


Scenario Testing
----------------

For specific server scenarios, leave both mock options disabled and send one
of the API's documented service names explicitly. The most useful values are:

* ``test_success`` — immediately completed verification or active rental.
* ``test_delayed_success`` and ``test_pending`` — verification polling flows.
* ``test_timeout`` and ``test_reactivatable`` — verification terminal states.
* ``test_renewable_expired`` and ``test_nonrenewable_expired`` — expired rental flows.
* ``test_backorder`` — rental backorder flow; requires
  ``allow_back_order_reservations=True``.
* ``test_insufficient_balance``, ``test_no_numbers``, and
  ``test_too_many_unfinished_verifications`` — error handling flows.

For example, use ``service_name="test_pending"`` to exercise cancellation and
reporting behavior. Do not enable ``mock_api`` for a custom scenario,
because mock mode intentionally replaces the supplied name with ``test_success``.
