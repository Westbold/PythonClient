from textverified import services, verifications, sms
from textverified.data import NumberType, ReservationType, ReservationCapability

# List available services
services_list = services.get_services(number_type=NumberType.MOBILE, reservation_type=ReservationType.VERIFICATION)
print("Available Services:", sorted({services_list.service_name for services_list in services_list}))

# Create a verification
verification = verifications.create_verification(
    service_name="servicenotlisted",
    capability=ReservationCapability.SMS,
)

print("Created number for verification:", verification.number)

# Show the next incoming SMS for the verification
print("Waiting for incoming SMS...")
print("Verification Codes:", next(sms.incoming_sms(verification, timeout=-1)))


# ------ #

