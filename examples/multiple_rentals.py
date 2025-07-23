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
            always_on=True,  # For wakeable numbers, be sure to make a wake request before expecting sms
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
    all_messages = client.sms.list()  # you can also use client.sms.incoming() for real-time polling
    for message in all_messages:
        if message.to_value in my_numbers:
            print(f"Received SMS from {message.from_value} to {message.to_value}: {message.sms_content}")
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
