Quick Start Guide
================

This guide will help you get started with the TextVerified Python client.

Installation
------------

Install the package using pip:

.. code-block:: bash

   pip install textverified

Authentication
--------------

You'll need your TextVerified API credentials. You can get these from your TextVerified dashboard.

There are two ways to authenticate:

Method 1: Environment Variables (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set your credentials as environment variables:

.. code-block:: bash

   export TEXTVERIFIED_API_KEY="your_api_key"
   export TEXTVERIFIED_API_USERNAME="your_username"

Then use the static API:

.. code-block:: python

   from textverified import account as tv_account

   # Get account details
   account_info = tv_account.me()
   print("Username:", account_info.username)
   print("Balance:", account_info.current_balance)

Method 2: Configure Client Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set your credentials by calling textverified.configure():

.. code-block:: python

   import textverified

   textverified.configure(
       api_key="your_api_key",
       api_username="your_username"
   )

Then use the static API:

.. code-block:: python

   from textverified import account as tv_account
   
   # Get account details
   account_info = tv_account.me()
   print("Username:", account_info.username)
   print("Balance:", account_info.current_balance)

Method 3: Direct Instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a client instance with your credentials:

.. code-block:: python

   from textverified import TextVerified

   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username"
   )
   
   # Get account details
   account_info = client.account.me()
   print("Username:", account_info.username)
   print("Balance:", account_info.current_balance)

Basic Usage Examples
-------------------

Listing Services
~~~~~~~~~~~~~~~~
Remember to list available services before creating verifications or rentals, as the number of available services
increases frequently.

.. code-block:: python

   from textverified import services
   from textverified import NumberType, ReservationType

   # Get available services, by number type and reservation type
   all_services = services.list(
      number_type=NumberType.MOBILE,  # or .VOIP
      reservation_type=ReservationType.VERIFICATION,  # or .RENEWABLE or .NONRENEWABLE
   )

   for service in all_services:
      print(f"Service: {service.service_name}")

Creating a Verification
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import verifications, ReservationCapability

   # Create a verification for a specific service
   verification = verifications.create(
      service_name="yahoo",
      capability=ReservationCapability.SMS,
   )

   print(f"Phone number: {verification.number}")
   print(f"Verification ID: {verification.id}")

Getting SMS Messages
~~~~~~~~~~~~~~~~~~~
You can retrieve SMS messages received by your rented numbers and verifications.
To filter by a specific rental or verification, pass it into sms.list()

.. code-block:: python

   from textverified import sms

   messages = sms.list()

   for message in messages:
      print(f"From: {message.from_value}")
      print(f"To: {message.to_value}")
      print(f"Time: {message.created_at}")
      print(f"Message: {message.sms_content}")

Account Information
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import account

   account_info = account.me()

   print(f"Username: {account_info.username}")
   print(f"Balance: ${account_info.current_balance}")

Error Handling
--------------

The client includes proper error handling:

.. code-block:: python

   from textverified import verifications
   from textverified import TextVerifiedError

   try:
      verification = verifications.create(
         service_name="Tyrell Corporation",  # Invalid service name
         capability=ReservationCapability.SMS,
      )
   except TextVerifiedError as e:
      print(f"Error: {e}")
   except Exception as e:
      print(f"Unexpected error: {e}")

Some endpoints, such as  verification/rental pricing and verification/rental creation,
may not support all combinations of parameters. In these cases, the API will return an error.

Next Steps
----------

- Check out the :doc:`api_reference` for detailed API documentation
- See :doc:`examples` for more comprehensive usage examples
- Visit the `TextVerified website <https://textverified.com>`_ for more information
