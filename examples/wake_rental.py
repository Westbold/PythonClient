from textverified import reservations, wake_requests, sms, NumberType, ReservationCapability, RentalDuration
import datetime

# 1. Create a wakeable (non-always-on) rental
reservation = reservations.create(
    service_name="allservices",
    number_type=NumberType.MOBILE,
    capability=ReservationCapability.SMS,
    is_renewable=False,
    always_on=False,
    duration=RentalDuration.THIRTY_DAY,
    allow_back_order_reservations=False,
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
