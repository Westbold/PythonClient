# TextVerified Python Client

A Python wrapper for the TextVerified API, providing easy access to phone number verification services.

## Installation

```bash
pip install textverified
```

## Quick Start

```python
from textverified import TextVerified

# Initialize client
client = TextVerified(
    api_key="your_api_key",
    api_username="your_username"
)

# List available services
services = client.services.list()

# Create a verification
verification = client.verifications.create(service_id=1)
print(f"Phone number: {verification.number}")

# Get SMS messages
messages = client.sms.get_sms(verification_id=verification.id)
```

## Documentation

Comprehensive documentation is available and includes:

- **API Reference**: Complete documentation of all classes and methods
- **Quick Start Guide**: Get up and running quickly
- **Examples**: Real-world usage examples and patterns
- **Error Handling**: Best practices for robust applications

### Building Documentation Locally

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
sphinx-build -b html . _build/html
```

The built documentation will be available at `docs/_build/html/index.html`.

### Online Documentation

The latest documentation is automatically built and deployed to GitHub Pages on every release.

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/Westbold/PythonClient.git
cd PythonClient

# Install in development mode with all dependencies
pip install -e ".[dev,docs]"

# Run tests
pytest

# Build documentation
./build-docs.sh  # or build-docs.bat on Windows
```

### Development Dependencies

The documentation is built using:

- **Sphinx**: Documentation generator
- **sphinx-rtd-theme**: Read the Docs theme

## Features

- Complete API coverage for TextVerified services
- Type hints for better IDE support
- Comprehensive error handling
- Both instance-based and static usage patterns
- Pagination support for large result sets
- Detailed documentation and examples

## API Coverage

- ✅ Account Management
- ✅ Service Listings
- ✅ Phone Number Verifications
- ✅ SMS Message Retrieval
- ✅ Reservations
- ✅ Sales Management
- ✅ Billing Cycles
- ✅ Wake Requests

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For support, please contact Westbold LLC or visit [TextVerified.com](https://textverified.com).
