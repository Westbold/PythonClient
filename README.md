# TextVerified Python Library

[![PyPI version](https://img.shields.io/pypi/v/textverified.svg)](https://pypi.python.org/pypi/textverified/)
[![Issues](https://img.shields.io/github/issues/Westbold/PythonClient.svg)](https://github.com/Westbold/PythonClient/issues)
[![Documentation Status](https://readthedocs.org/projects/textverified/badge/?version=latest)](https://textverified.readthedocs.io/)

This library eases the use of the TextVerified REST API from Python and provides a comprehensive interface for phone number verification services. It has been designed for production use and includes robust error handling, type hints, and extensive documentation.


## Installation

Download and install using 

```
pip install textverified
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
import time

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

# 3. Wait for and retrieve SMS messages
print("Waiting for SMS messages...")
time.sleep(30)  # Wait for messages to arrive

messages = client.sms.list(verification_id=verification.id)
for message in messages:
    print(f"Received: {message.sms_content}")
```

### Account Management

```python
from textverified import account

# Get account information
account_info = account.me()
print(f"Username: {account_info.username}")
print(f"Balance: ${account_info.current_balance}")
print(f"Total spent: ${account_info.total_spent}")
```

### Service Discovery

```python
from textverified import services, NumberType, ReservationType

# Get all mobile verification services
mobile_services = services.list(
    number_type=NumberType.MOBILE,
    reservation_type=ReservationType.VERIFICATION
)

# Filter services by name
yahoo_services = [s for s in mobile_services if 'yahoo' in s.service_name.lower()]

for service in yahoo_services:
    print(f"Service: {service.service_name}")
    print(f"Capability: {service.capability}")
    print(f"Countries: {len(service.countries)} available")
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

### Bulk Operations

```python
from textverified import verifications, sms

# Create multiple verifications
verification_requests = [
    {"service_name": "yahoo", "capability": "SMS"},
    {"service_name": "google", "capability": "SMS"},
    {"service_name": "facebook", "capability": "SMS"}
]

created_verifications = []
for request in verification_requests:
    try:
        verification = verifications.create(**request)
        created_verifications.append(verification)
        print(f"Created verification for {request['service_name']}: {verification.number}")
    except TextVerifiedError as e:
        print(f"Failed to create verification for {request['service_name']}: {e}")

# Check for messages across all verifications
all_messages = sms.list()
print(f"Total messages received: {len(all_messages)}")
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

For support, please contact [Westbold LLC](mailto:support@westbold.com) or visit [TextVerified.com](https://textverified.com).
