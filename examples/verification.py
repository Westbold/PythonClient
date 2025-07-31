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
        reservation_type=ReservationType.VERIFICATION,  # or ReservationType.RENEWABLE or ReservationType.NONRENEWABLE
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
