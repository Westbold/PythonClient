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

   from textverified import services, verifications
   
   # List available services
   services_list = services.list()
   
   # Create a verification
   verification = verifications.create(service_id=1)

Method 2: Direct Instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a client instance with your credentials:

.. code-block:: python

   from textverified import TextVerified
   
   client = TextVerified(
       api_key="your_api_key",
       api_username="your_username"
   )
   
   # List available services
   services_list = client.services.list()
   
   # Create a verification
   verification = client.verifications.create(service_id=1)

Basic Usage Examples
-------------------

Listing Services
~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import services
   
   # Get all available services
   all_services = services.list()
   
   for service in all_services:
       print(f"Service: {service.name} (ID: {service.id})")

Creating a Verification
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import verifications
   
   # Create a verification for a specific service
   verification = verifications.create(service_id=1)
   
   print(f"Phone number: {verification.number}")
   print(f"Verification ID: {verification.id}")

Getting SMS Messages
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import sms
   
   # Get SMS messages for a verification
   messages = sms.get_sms(verification_id=12345)
   
   for message in messages:
       print(f"From: {message.sender}")
       print(f"Message: {message.message}")
       print(f"Time: {message.time}")

Account Information
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from textverified import account
   
   # Get account information
   account_info = account.me()
   
   print(f"Username: {account_info.username}")
   print(f"Balance: ${account_info.balance}")

Error Handling
--------------

The client includes proper error handling:

.. code-block:: python

   from textverified import verifications
   from textverified.textverified import TextVerifiedException
   
   try:
       verification = verifications.create(service_id=999)  # Invalid service
   except TextVerifiedException as e:
       print(f"Error: {e}")
   except Exception as e:
       print(f"Unexpected error: {e}")

Next Steps
----------

- Check out the :doc:`api_reference` for detailed API documentation
- See :doc:`examples` for more comprehensive usage examples
- Visit the `TextVerified website <https://textverified.com>`_ for more information
