# TextVerified Python Library

[![PyPI version](https://img.shields.io/pypi/v/textverified.svg)](https://pypi.python.org/pypi/textverified/)
[![Issues](https://img.shields.io/github/issues/Westbold/PythonClient.svg)](https://github.com/Westbold/PythonClient/issues)
[![Documentation Status](https://readthedocs.org/projects/textverified-python/badge/?version=latest)](https://textverified-python.readthedocs.io/en/latest/)

This library eases the use of the TextVerified REST API from Python and provides a comprehensive interface for phone number verification services. It has been designed for production use and includes robust error handling, type hints, and extensive documentation.


## Installation

Download and install using 

```
pip install textverified
```

If you're on an older version of python (`<3.11`), install `tomli` first:
```
pip install tomli
```

## Features

- **Complete API Coverage**: All TextVerified endpoints are supported
- **Type Hints**: Full type annotation support for better IDE experience
- **Error Handling**: Comprehensive exception handling with specific error types
- **Dual Usage Patterns**: Support for both instance-based and static usage
- **Pagination**: Automatic handling of paginated results
- **Production Ready**: Robust error handling and retry mechanisms


## Quickstart

### Authentication

You'll need your TextVerified API credentials. You can get these from your TextVerified dashboard.

There are two ways to authenticate:

**Method 1: Environment Variables (Recommended)**

```bash
export TEXTVERIFIED_API_KEY="your_api_key"
export TEXTVERIFIED_API_USERNAME="your_username"
```

Then use the static API:

```python
from textverified import account as tv_account

# Get account details
account_info = tv_account.me()
print("Username:", account_info.username)
print("Balance:", account_info.current_balance)
```

**Method 2: Configure Client Directly**

Set your credentials by calling textverified.configure():

```python
import textverified

textverified.configure(
    api_key="your_api_key",
    api_username="your_username"
)
```

Then use the static API:

```python
from textverified import account as tv_account

# Get account details
account_info = tv_account.me()
print("Username:", account_info.username)
print("Balance:", account_info.current_balance)
```

**Method 3: Direct Instantiation**

You can create an instance of the client,
this also provides better type hinting.

```python
from textverified import TextVerified

client = TextVerified(
    api_key="your_api_key",
    api_username="your_username"
)

# Get account details
account_info = client.account.me()
print("Username:", account_info.username)
print("Balance:", account_info.current_balance)
```

## Examples

### Complete Verification Workflow

```python
from textverified import TextVerified, NumberType, ReservationType, ReservationCapability
import time, datetime

# Initialize client
client = TextVerified(api_key="your_api_key", api_username="your_username")

# 1. List available services
services = client.services.list(
    number_type=NumberType.MOBILE,
    reservation_type=ReservationType.VERIFICATION
)

print(f"Found {len(services)} available services")
for service in services[:5]:  # Show first 5
    print(f"  {service.service_name}")

# 2. Create a verification
verification = client.verifications.create(
    service_name="yahoo",
    capability=ReservationCapability.SMS
)

print(f"Verification created: {verification.id}")
print(f"Phone number: {verification.number}")

# 3. Do something that sends a message to your number
time.sleep(10)

# 4. Wait for an incoming verification
messages = client.sms.incoming(
    verification,
    timeout=300,
    since=datetime.fromtimestamp(0)
)
for message in messages:
    print(f"Received: {message.sms_content}")
```

### Waking Lines

```python
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
```

### Error Handling

```python
from textverified import verifications, TextVerifiedError

try:
    verification = verifications.create(
        service_name="invalid_service",
        capability="SMS"
    )
except TextVerifiedError as e:
    print(f"TextVerified API Error: {e}")
    # Handle specific TextVerified errors
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other exceptions
```

## Documentation

See the [documentation](https://textverified.readthedocs.io/) for full details, including:

- **API Reference**: Complete documentation of all classes and methods  
- **Quick Start Guide**: Get up and running quickly
- **Examples**: Real-world usage examples and patterns
- **Error Handling**: Best practices for robust applications

## TextVerified API Reference Links

When working with the TextVerified API, please refer to the official documentation:

1. [TextVerified API Documentation](https://www.textverified.com/docs/api/v2) - Main REST API reference
2. [TextVerified Dashboard](https://www.textverified.com/app/api/configure) - Manage your account and view usage
3. [TextVerified Support](https://www.textverified.com/app/support) - Get help and contact support

## Credits

This library is developed and maintained by **Westbold LLC**.

Special thanks to:

* **TextVerified** for providing a reliable phone verification service and comprehensive API
* **Python Community** for the excellent tools and libraries that make this project possible
* **Our Users** for feedback and contributions that help improve the library

For support, please open a ticket at [TextVerified Support](https://www.textverified.com/app/support)
