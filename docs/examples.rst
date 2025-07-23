Examples
========

This section provides comprehensive examples of using the TextVerified Python client.

Complete Verification Workflow
------------------------------

Here's a complete example that demonstrates the a full verification workflow:

.. code-block:: python

    from textverified import TextVerified
    from textverified import NumberType, ReservationType, ReservationCapability, NewVerificationRequest
    import time

    # Initialize client
    client = TextVerified(api_key="your_api_key", api_username="your_username")

    def complete_verification_example():
        """Complete example of phone verification workflow."""

        # 1. List available services
        print("Available services:")
        services = client.services.list(
            number_type=NumberType.MOBILE,  # or NumberType.VOIP
            reservation_type=ReservationType.VERIFICATION,  # or .RENEWABLE or .NONRENEWABLE
        )

        for service in services[:5]:  # Show first 5
            print(f"  {service.service_name} (Capability: {service.capability})")

        # 2. Create pricing estimate and verify availability
        service_name = services[0].service_name  # Use the first service for this example
        request = NewVerificationRequest(
            service_name=service_name,
            capability=ReservationCapability.SMS,
        )

        print(f"\nPricing estimate for {service_name}:")
        price = client.verifications.pricing(request)
        print(f"  Estimated cost: ${price.price}")

        # 3. Create a verification
        print(f"\nCreating verification for service '{service_name}'...")
        verification = client.verifications.create(request)
        print(f"Verification created successfully: {verification.id}")

        # 4. Receive a verification code to the provided phone number
        print(f"Waiting for SMS messages to number {verification.number}...")
        # It's your job to send a verification within its validity period

        # 5. Poll for SMS messages
        messages = client.sms.incoming(verification, timeout=300)  # Verifications last 5 minutes
        message = next(messages)

        # 6. Return the received verification code
        print("Received verification code:", message.parsed_code)
        return message.parsed_code


    # Run the example
    if __name__ == "__main__":
        complete_verification_example()


Account Management
------------------

Managing your account and billing:

.. code-block:: python

    from textverified import account, billing_cycles


    # Get account information
    account_info = account.me()
    print("Account Details:")
    print(f"  Username: {account_info.username}")
    print(f"  Balance: ${account_info.current_balance}")

    # Get billing cycles
    cycles = billing_cycles.list()
    print("\nBilling Cycles:")

    for cycle in cycles[:3]:  # Show last 3 cycles
        print(f"  Cycle ID: {cycle.id}")
        print(f"  Ends At: {cycle.billing_cycle_ends_at}")
        print(f"  State: {cycle.state}")
        print("  ---")


Bulk Rental Processing / Management
---------------------------

Processing multiple rentals efficiently:

.. code-block:: python

    import pickle
    from textverified import TextVerified, NumberType, ReservationCapability, RentalDuration

    # Data structure to store reservations
    reservations = list()


    # Save rentals to disk
    def save_rentals_to_disk(file_path="rentals.pkl"):
        with open(file_path, "wb") as file:
            pickle.dump(reservations, file)


    # Load rentals from disk
    def load_rentals_from_disk(file_path="rentals.pkl"):
        global reservations
        try:
            with open(file_path, "rb") as file:
                reservations = pickle.load(file)
        except FileNotFoundError:
            print("No existing reservations file found. Starting fresh.")


    # Create nonrenewable rentals and add to data structure
    def create_rentals(client, count=5):
        for _ in range(count):
            reservation = client.reservations.create(
                service_name="allservices",
                number_type=NumberType.MOBILE,
                capability=ReservationCapability.SMS,
                is_renewable=True,
                duration=RentalDuration.THIRTY_DAY,
                always_on=True,  # If false, make a wake request before expecting sms
                allow_back_order_reservations=False,
            ).reservations[0]
            
            # Expand reservation to get full details
            rental = client.reservations.details(reservation)
            
            # Store
            reservations.append(rental)
            print(f"Created reservation {rental.id} for number {rental.number}")
        save_rentals_to_disk()


    # Receive SMS for all rentals
    def receive_sms_for_all(client):
        my_numbers = [reservation.number for reservation in reservations]
        all_messages = client.sms.list() # you can also use client.sms.incoming() for real-time polling
        for message in all_messages:
            if message.to_value in my_numbers:
                print(
                      f"Received SMS from {message.from_value} to {message.to_value}:"
                      f" {message.sms_content}"
                )
                # Process the message as needed, e.g., store or display it


    # Example usage
    if __name__ == "__main__":
        client = TextVerified(api_key="your_api_key", api_username="your_username")
        
        load_rentals_from_disk()
        
        # Create rentals
        create_rentals(client, count=3)
        
        # Print your numbers
        print("Your rentals:")
        for rental in reservations:
            print(f"Number: {rental.number}, State: {rental.state}")
        

        # Do something with the rentals!
        import time
        time.sleep(10)  # Simulate waiting for messages

        # Receive SMS for all verifications
        receive_sms_for_all(client)


Wakeable Rental Example
-----------------------

.. code-block:: python

    import datetime
    from textverified import (
        reservations, wake_requests, sms,
        NumberType, ReservationCapability, RentalDuration
    )

    # 1. Create a wakeable (non-always-on) rental
    reservation = reservations.create(
        service_name="allservices",
        number_type=NumberType.MOBILE,
        capability=ReservationCapability.SMS,
        is_renewable=False,
        always_on=False,
        duration=RentalDuration.THIRTY_DAY,
        allow_back_order_reservations=False
    ).reservations[0]
    rental = reservations.details(reservation)
    print(f"Reserved number {rental.number} with id {rental.id}")

    # 2. Start a wake request for the rental
    print("Sending wake request and waiting for active window...")
    wake_request = wake_requests.create(rental)
    duration = wake_request.usage_window_end - wake_request.usage_window_start
    print(
        f"Number {rental.number} is active from {wake_request.usage_window_start}"
        f" to {wake_request.usage_window_end} (duration: {duration})"
    )

    # 3. Wait for the wake request to complete
    time_until_start = wake_request.usage_window_start - datetime.datetime.now(datetime.timezone.utc)
    print(f"Waiting for the number to become active... ({time_until_start})")
    wake_response = wake_requests.wait_for_wake_request(wake_request)


    # 3. Poll for SMS messages on the awakened number
    print(f"Polling SMS messages for number {rental.number}...")
    messages = sms.incoming(rental, timeout=duration.total_seconds())
    for msg in messages:
        print(f"Received SMS from {msg.from_value}: {msg.sms_content}")

Error Handling Patterns
----------------------

Proper error handling for production use:

.. code-block:: python

    from textverified import TextVerified, verifications
    from textverified.textverified import TextVerifiedException
    import requests
    import time
      
    try:
        # Attempt to create verification
        verification = verifications.create(
            service_name="yahoo",
            capability=ReservationCapability.SMS,
        )
        print(f"Verification created successfully: {verification.id}")
        return verification
        
    except TextVerifiedException as e:
        print(f"TextVerified API error (attempt {attempt + 1}): {e}")
        break
        
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error (attempt {attempt + 1}): {e}")
        
    except requests.exceptions.Timeout as e:
        print(f"Timeout error (attempt {attempt + 1}): {e}")
        
    except Exception as e:
        print(f"Unexpected error (attempt {attempt + 1}): {e}")

Note that all API requests use exponential backoff for retries, and retries on connection error or ratelimit errors.

