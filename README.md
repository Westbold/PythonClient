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

## Optional terminal application

Install the optional terminal app (Python 3.10+):

```sh
pip install "textverified[tui]"
```

For this feature, use `pip install -e ".[tui]"`. The `tv` and `textverified`
commands run the same app; `python -m textverified.terminal` also works.

The app provides an inline home screen, service matching, purchase confirmation,
an animated waiting card and code results.
For a real account:

```sh
tv login
tv balance
tv services discord
tv --mock verify discord
tv verify discord
tv logout
```

Login asks for Email and a hidden API key, validates them, then saves to
`~/.cache/textverified/credentials.json` (or `$XDG_CACHE_HOME/textverified/`).
The cache is plaintext, with owner-only file permissions on Unix.
`TEXTVERIFIED_CONFIG_DIR` places it under that directory's `cache/` folder.
A complete `TEXTVERIFIED_API_USERNAME` / `TEXTVERIFIED_API_KEY` pair overrides it.

Purchases require confirmation or `--yes`, and use the quoted price as a
server-side cap. Piped verification output ends with the bare code. Use `--no-animation`
for a static badge; `TV_THEME=light` selects light-terminal text colors.
The logo uses half-blocks by default, and finer sextants on supported terminals.
Set `TV_BADGE=blocky` or `TV_BADGE=fine` to choose the renderer.
`--mock` uses the SDK's `TestMode.MOCK_SUCCESS` for pricing and creation, and
selects server mock resources for inbox, polling and rental commands. You can run
`tv --mock poll` without a reservation ID or `--since`; fixed mock SMS timestamps
are included. Use `--type renewable` or `--type nonrenewable` to poll a mock rental.
Explicit `mock_*` IDs are preserved; other IDs/numbers are overridden in mock mode.
Credentials and network access are still required. Authentication, account and
service-catalog operations retain the SDK's normal behavior. Endpoints without
server mock support report the API error; the CLI does not fabricate responses.


Output defaults to `--color=auto`: terminal colors and animations are automatic;
pipes and redirected files have no animations or ANSI colors. Use `--color=always`
to force colors on a terminal, or `--color=never` to disable them. Redirected
output remains plain even with `--color=always`. Inbox and polling use tables in a terminal and tab-separated
records when piped, preserving full SMS bodies without terminal-width wrapping.

```sh
tv inbox > inbox.tsv
tv poll --follow --timeout -1 | tee messages.tsv
tv --color=always inbox
```

The unified inbox includes SMS bodies across verification and rental lines. Poll
for any incoming SMS or filter by reservation ID, line ID, number, and type:

```sh
tv inbox
tv inbox --line-number 14155550123
tv poll --timeout 60
tv poll --line-id RENTAL_ID --type renewable
tv poll --reservation-id VERIFICATION_ID --type verification
tv poll --number 14155550123 --follow --timeout -1
tv verifications list
tv verifications show VERIFICATION_ID
tv verifications resume VERIFICATION_ID
tv verifications cancel VERIFICATION_ID
tv verify gmail --area-code 415 --carrier att
```

Rental commands support both renewable and nonrenewable lines:

```sh
tv rentals
tv rentals services gmail --kind nonrenewable
tv rentals price gmail --kind nonrenewable --duration sevenDay
tv rentals price gmail --number-type voip
tv rentals buy gmail --kind nonrenewable --duration sevenDay
tv rentals show RENTAL_ID
tv rentals sale SALE_ID
tv rentals wake RENTAL_ID --wait
tv rentals extend RENTAL_ID --duration sevenDay
tv rentals renew OVERDUE_RENEWABLE_ID
tv rentals update RENTAL_ID --notes "work line" --tags work
```

Purchases and renewal, extension, reactivation and refund actions require
confirmation or `--yes`. Rentals must be always on or awake to receive SMS.
Existing verifications can be inspected, resumed and explicitly cancelled.
Verification and rental lists default to five recent entries total, with creation
time last in the local timezone. Use `list --limit N` for a larger list and
`show ID` for full details. IDs remain in piped TSV output.
Inbox snapshots and service catalogs also default to five entries; use
`inbox --limit N`, `services --limit N` or `rentals services --limit N` to expand
them. Inbox and poll tables put local received time last. Piped SMS columns are
`ID`, `To`, `From`, `Code`, `Body`, `Received`, preserving complete bodies.
Polling continues to stream all incoming messages.
Every command with `--limit` also accepts `--offset N` (default 0), skipping N
matching entries before the limit. For example, `tv inbox --offset 5 --limit 5`
shows the next five messages; `tv rentals list --offset 5 --limit 5` skips five
entries across both rental types.
If creation succeeds but fetching details fails, the CLI reports acceptance
and a recovery command; inspect the existing purchase before retrying.
Rental and service lists and verification lists/details emit TSV when piped,
while failures go to stderr.
See [terminal usage, integration and tests](docs/terminal.rst) for all commands.
For automation, see [advanced piping examples](docs/terminal_scripting.rst),
including streaming SMS into scripts, preserving multiline bodies, extracting
codes and checking pipeline failures.

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



## Documentation

See the [documentation](https://textverified.readthedocs.io/) for full details, including:

- **API Reference**: Complete documentation of all classes and methods  
- **Quick Start Guide**: Get up and running quickly
- **Examples**: Real-world usage examples and patterns
- **Error Handling**: Best practices for robust applications

## Support and Resources

When working with the TextVerified API, please refer to the official documentation:

1. [TextVerified API Documentation](https://www.textverified.com/docs/api/v2) - Main REST API reference
2. [TextVerified Dashboard](https://www.textverified.com/app/api/configure) - Manage your account and view usage
3. [TextVerified Support](https://www.textverified.com/app/support) - Get help and contact support

For support, please open a ticket at [TextVerified Support](https://www.textverified.com/app/support)

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
