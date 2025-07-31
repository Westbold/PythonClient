# Make sure you have the textverified package installed
# pip install textverified

# Credentials are required to use the TextVerified API.
# They are automatically loaded from the environment variables
# TEXTVERIFIED_API_KEY and TEXTVERIFIED_API_USERNAME.
# or can be set using the configure method.


# --- List Services ---
from textverified import services
from textverified import NumberType, ReservationType

# Get available services, by number type and reservation type
all_services = services.list(
    number_type=NumberType.MOBILE,  # or NumberType.VOIP
    reservation_type=ReservationType.VERIFICATION,  # or ReservationType.RENEWABLE or ReservationType.NONRENEWABLE
)

for service in all_services:
    print(f"Service: {service.service_name}")

# --- Create a Verification ---
from textverified import verifications, ReservationCapability

# Create a verification for a specific service
verification = verifications.create(
    service_name="yahoo",
    capability=ReservationCapability.SMS,
)

print(f"Phone number: {verification.number}")
print(f"Verification ID: {verification.id}")

# --- List SMS messages ---
from textverified import sms

messages = sms.list()

for message in messages:
    print(f"From: {message.from_value}")
    print(f"To: {message.to_value}")
    print(f"Time: {message.created_at}")
    print(f"Message: {message.sms_content}")


# --- Get Account Details ---
from textverified import account

account_info = account.me()

print(f"Username: {account_info.username}")
print(f"Balance: ${account_info.current_balance}")


# --- Error Handling ---
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
