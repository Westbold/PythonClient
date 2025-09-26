"""
Mocking Examples for TextVerified Python Client

This example demonstrates how to use mock verification and rental IDs
in real API workflows for testing and development.
"""

from textverified import TextVerified, mocking, MockBehavior, MockReceivePolicy, ReservationCapability, NewVerificationRequest
import time

client = TextVerified(api_key="YOUR_KEY", api_username="YOUR_EMAIL")

def mock_verification_workflow():
    """Complete verification workflow using a mock verification ID."""
    print("Mock Verification Workflow")
    print("=" * 30)

    # Create a mock verification
    mock_verification = mocking.verification(receive_policy=MockReceivePolicy.IncomingText) # default behavior, but explicitly specified
    print(f"Created mock verification: {mock_verification.id}")

    try:
        # Use the real client for verification details and state
        verification = client.verifications.details(mock_verification.id)
        print(f"Verification number: {verification.number}")
        print(f"Verification state: {verification.state}")

        # Poll for SMS messages with base
        print("Polling for SMS messages...")
        messages = client.sms.incoming(verification, timeout=10)
        for message in messages:
            print(f"Received SMS: {message.sms_content}")
            print(f"Parsed code: {message.parsed_code}")

    except Exception as e:
        print(f"API call failed (expected with mock credentials): {type(e).__name__}")

    print()


def mock_verification_purchase_workflow():
    """Verification purchase workflow using a mock service name."""
    print("Mock Verification Purchase Workflow")
    print("=" * 30)

    # Create a mock service name (target)
    # You can also use mocking.service(...) as an alias
    mock_service = mocking.target(behavior=MockBehavior.Succeeds)
    print(f"Created mock service: {mock_service}")

    try:
        # Create a verification request using the mock service name
        request = NewVerificationRequest(
            service_name=mock_service,
            capability=ReservationCapability.SMS
        )

        # Get pricing for the mock service
        price = client.verifications.pricing(request)
        print(f"Pricing for mock service: ${price.price}")

        # Create the verification
        verification = client.verifications.create(request)
        print(f"Verification created: {verification.id}")
        print(f"Verification number: {verification.number}")

        # Poll for SMS messages
        print("Polling for verification code...")
        for message in client.sms.incoming(verification, timeout=10):
            print(f"Received SMS: {message.sms_content}")
            print(f"Parsed verification code: {message.parsed_code}")
            break

    except Exception as e:
        print(f"API call failed (expected with mock credentials): {type(e).__name__}")

    print()


def mock_verification_with_random_failures():
    """Verification workflow that may fail randomly to test error handling."""
    print("Mock Verification with Random Failures")
    print("=" * 30)

    # Create a mock verification that fails randomly (1/3 of the time)
    # This helps test unexpected behavior and error handling
    mock_verification = mocking.verification(
        behavior=MockBehavior.FailsRandomly,
        receive_policy=MockReceivePolicy.IncomingText
    )
    print(f"Created mock verification: {mock_verification.id}")

    try:
        verification = client.verifications.details(mock_verification.id)
        print(f"Verification succeeded: {verification.number}")

        # This might succeed or fail, testing your error handling
        for message in client.sms.incoming(verification, timeout=10):
            print(f"SMS received: {message.parsed_code}")

    except Exception as e:
        print(f"Verification failed (this may happen randomly): {type(e).__name__}")

    print()


def mock_rental_workflow():
    """Rental workflow using a mock rental ID."""
    print("Mock Rental Workflow")
    print("=" * 30)

    # Create a mock rental
    mock_rental = mocking.rental(behavior=MockBehavior.Succeeds)
    print(f"Created mock rental: {mock_rental.id}")

    client = TextVerified(api_key="mock", api_username="mock")

    try:
        # Get rental details
        rental = client.reservations.details(mock_rental.id)
        print(f"Rental number: {rental.number}")
        print(f"Rental state: {rental.state}")

        # List SMS messages for the rental
        messages = client.sms.list()
        print(f"Found {len(messages)} SMS messages")

    except Exception as e:
        print(f"API call failed (expected with mock credentials): {type(e).__name__}")

    print()


def mock_wake_rental_workflow():
    """Wake rental workflow using a mock rental ID."""
    print("Mock Wake Rental Workflow")
    print("=" * 30)

    # Create a mock rental for wake testing
    mock_rental = mocking.rental(
        behavior=MockBehavior.Succeeds,
        receive_policy=MockReceivePolicy.IncomingTextAndCall
    )
    print(f"Created mock rental: {mock_rental.id}")

    try:
        # Get rental details
        rental = client.reservations.details(mock_rental.id)
        print(f"Rental number: {rental.number}")

        # Create a wake request for the rental
        wake_request = client.wake_requests.create(rental)
        print(f"Wake request created: {wake_request.id}")
        print(f"Active from {wake_request.usage_window_start} to {wake_request.usage_window_end}")

        # Poll for messages during the wake window
        duration = wake_request.usage_window_end - wake_request.usage_window_start
        print("Polling for messages during wake window...")
        messages = client.sms.incoming(rental, timeout=duration.total_seconds())

        for message in messages:
            print(f"Received: {message.sms_content}")
            break  # Just show first message

    except Exception as e:
        print(f"API call failed (expected with mock credentials): {type(e).__name__}")

    print()


if __name__ == "__main__":
    print("TextVerified Mocking Examples")
    print("=" * 30)
    print()

    # Run all examples
    mock_verification_workflow()
    mock_verification_purchase_workflow()
    mock_verification_with_random_failures()
    mock_rental_workflow()
    mock_wake_rental_workflow()

    print("Examples completed.")
    print("Note: API calls use mock credentials and may fail - this demonstrates")
    print("how mock IDs integrate with real API workflows for testing.")
