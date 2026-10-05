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

Install the full-screen TUI and scriptable CLI separately from the lightweight SDK:

```sh
pip install "textverified[tui]"
```

For this checkout, use `pip install -e ".[tui]"`. The terminal extra requires
Python 3.10 or newer. A plain `pip install textverified` keeps Textual, Typer,
keyring and terminal-specific dependencies out of the base installation.

Run the TUI and sign in with your **Email and API key**. Validated credentials
are saved automatically to `~/.cache/textverified/credentials.json` (or
`$XDG_CACHE_HOME/textverified/credentials.json`) for future sessions. You can
also log in from the CLI:

```sh
textverified auth login
textverified tui
```

`textverified tui` opens **Numbers** with active verifications first, then active
renewable/nonrenewable rentals and history. **Inbox** receives account-wide SMS,
including retained messages for inactive numbers and numbers bought elsewhere.
The header shows your account, credit balance and connection state; the footer
shows keyboard controls. Purchase forms fetch a quote and require a separate
confirmation. Viewing or watching messages never purchases or wakes a number.

| Key | Action |
| --- | --- |
| `1` / `2` | Numbers / Inbox |
| `v` / `r` | Open verification / rental purchase form |
| `/` / `f` | Search / loaded versus API-history scope |
| Up / Down, Tab, Enter | Navigate, change focus, open details |
| `a` | Explicit resource actions |
| `c` / `n` / `y` | Copy code / number / message |
| `g` | Follow newest Inbox message |
| F5, `?`, Ctrl+P, `q` | Refresh, help, palette, quit |

Letter shortcuts do not fire while typing in editable fields. Use Ctrl+P for
account details, profile switching and themes. Clipboard support depends on the
terminal; full details provide selectable text when copying is unavailable.

```sh
textverified account show
textverified list --state active
textverified sms list --all --json
textverified sms watch --tail 0 --format ndjson
textverified sms wait --number +15550100101 --timeout 120 --code-only
textverified schema show verification.buy
textverified verification quote --service SERVICE --capability sms
textverified verification buy --service SERVICE --max-price 1.00 --yes --json
textverified rental quote --service SERVICE --duration 30d --no-renewable
textverified theme set terminal
textverified config path
```

Service names and numbers above are placeholders. `sms watch` replays the latest
20 messages by default; `--tail 0` starts after a silent completed baseline.
`wait` returns exit 8 on timeout. JSON uses schema version 1; watch uses flushed
NDJSON, with diagnostics on stderr. No saved profile or keyring is needed when
both environment credentials are supplied. Explicit `--profile` selects the
saved credential pair instead of environment credentials.

The default `textverified-dark` theme uses blue accents on a dark navy background.
A blue light preset, a terminal ANSI theme and custom TOML/TCSS are supported; recover with
`textverified tui --reset-style`. Metadata and purchase receipts use local
SQLite; SMS bodies, codes and API keys are not archived there. Use `config path`
to find settings and the credential cache. `TEXTVERIFIED_CONFIG_DIR` places
settings, state and a `cache/` folder together for portable use. Cached API keys
are local plaintext, with owner-only file permissions on Unix. Remove them with
`textverified auth logout`. Environment credentials and named profiles remain supported.

If the executable is missing, install the **tui extra in the same Python
environment**, or run `python -m textverified.terminal`. For noninteractive
sessions use CLI commands; the TUI requires an interactive terminal. For a
purchase with unknown outcome (exit 9), inspect recent resources and the local
operation receipt before buying again. Rental price limits are preflight only;
`--require-server-price-cap` rejects rental purchases. The pinned schema marks
rental receiving mode always-on and deprecates `alwaysOn`.

See the [terminal guide](docs/terminal.rst), [CLI reference](docs/terminal-cli.rst),
[theming guide](docs/terminal-themes.rst), and
[API compatibility notes](docs/api-compatibility.md) for configuration, output
contracts, server-dependent limitations, and verification status.

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