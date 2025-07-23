"""
TextVerified Python Client

This package provides a Python interface to the TextVerified API.
You can either use the TextVerified class directly to manage multiple credentials
or access API endpoints statically.

Example usage:
    from textverified import services, verifications
    # or
    from textverified import TextVerified
    client = TextVerified(api_key="...", api_username="...")
"""

import os
import sys
from typing import Optional

# Import the main TextVerified class and API modules
from .textverified import TextVerified, BearerToken
from .account_api import AccountAPI
from .billing_cycle_api import BillingCycleAPI
from .reservations_api import ReservationsAPI
from .sales_api import SalesAPI
from .services_api import ServicesAPI
from .sms_api import SMSApi
from .verifications_api import VerificationsAPI
from .wake_api import WakeAPI
from .paginated_list import PaginatedList
from .exceptions import TextVerifiedError

# Import generated enums
from .data import *

# Configurable, lazy-initialized static instance
_static_instance: Optional[TextVerified] = None


def _get_static_instance() -> TextVerified:
    """Get or create the static TextVerified instance."""
    global _static_instance
    if _static_instance is None:
        api_key = os.environ.get("TEXTVERIFIED_API_KEY")
        api_username = os.environ.get("TEXTVERIFIED_API_USERNAME")
        base_url = os.environ.get("TEXTVERIFIED_BASE_URL", "https://www.textverified.com")
        user_agent = os.environ.get("TEXTVERIFIED_USER_AGENT", "TextVerified-Python-Client/0.1.0")

        if not api_key or not api_username:
            raise ValueError(
                "TextVerified static instance not configured. "
                "Either call configure() or set TEXTVERIFIED_API_KEY and TEXTVERIFIED_API_USERNAME environment variables."
            )

        _static_instance = TextVerified(
            api_key=api_key, api_username=api_username, base_url=base_url, user_agent=user_agent
        )

    return _static_instance


def configure(
    api_key: str,
    api_username: str,
    base_url: str = "https://www.textverified.com",
    user_agent: str = "TextVerified-Python-Client/0.1.0",
) -> None:
    """Configure the static TextVerified instance."""
    global _static_instance
    _static_instance = TextVerified(
        api_key=api_key, api_username=api_username, base_url=base_url, user_agent=user_agent
    )


# Lazy property implementation using __getattr__ at module level
class _LazyAPI:
    """
    Lazy wrapper for API endpoints that creates the static TextVerified instance
    only when an API endpoint is actually accessed.
    """

    def __init__(self, attr_name: str, doc: str = None):
        self.attr_name = attr_name
        if doc:
            self.__doc__ = doc

    def __getattr__(self, name):
        """Forward attribute access to the actual API endpoint."""
        api_endpoint = getattr(_get_static_instance(), self.attr_name)
        return getattr(api_endpoint, name)

    def __call__(self, *args, **kwargs):
        """Forward method calls to the actual API endpoint."""
        api_endpoint = getattr(_get_static_instance(), self.attr_name)
        return api_endpoint(*args, **kwargs)


# Create lazy API wrappers with documentation
account = _LazyAPI(
    "account",
    """
Static access to account management functionality.

Provides methods for retrieving account information, balance, and account settings.
This is a static wrapper around the AccountAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import account
    
    # Get account information
    account_info = account.me()
    
    # Get account balance
    balance = account.balance()
""",
)

billing_cycles = _LazyAPI(
    "billing_cycles",
    """
Static access to billing cycle management functionality.

Provides methods for managing billing cycles, invoices, and payment history.
This is a static wrapper around the BillingCycleAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import billing_cycles
    
    # List all billing cycles
    cycles = billing_cycles.list()
    
    # Get specific billing cycle
    cycle = billing_cycles.get(cycle_id)
""",
)

reservations = _LazyAPI(
    "reservations",
    """
Static access to phone number reservation functionality.

Provides methods for creating, managing, and releasing phone number reservations.
This is a static wrapper around the ReservationsAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import reservations
    
    # Create a new reservation
    reservation = reservations.create(service_id=1, area_code="555")
    
    # List all reservations
    all_reservations = reservations.list()
""",
)

sales = _LazyAPI(
    "sales",
    """
Static access to sales and transaction functionality.

Provides methods for retrieving sales history, transaction details, and revenue analytics.
This is a static wrapper around the SalesAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import sales
    
    # Get sales history
    sales_history = sales.list()
    
    # Get specific sale details
    sale = sales.get(sale_id)
""",
)

services = _LazyAPI(
    "services",
    """
Static access to service management functionality.

Provides methods for listing available services, getting service pricing,
and retrieving service-specific information.
This is a static wrapper around the ServicesAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import services
    
    # Get all available services
    available_services = services.list()
    
    # Get pricing for rentals
    pricing = services.pricing_rentals()
""",
)

verifications = _LazyAPI(
    "verifications",
    """
Static access to phone verification functionality.

Provides methods for creating verification requests, checking verification status,
and managing the verification process.
This is a static wrapper around the VerificationsAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import verifications
    
    # Create a new verification
    verification = verifications.create(service_id=1)
    
    # Check verification status
    status = verifications.get(verification_id)
""",
)

wake_requests = _LazyAPI(
    "wake_requests",
    """
Static access to wake request functionality.

Provides methods for creating and managing wake requests for phone numbers.
This is a static wrapper around the WakeAPI class that uses the globally
configured TextVerified instance.

Example:
    from textverified import wake_requests
    
    # Create a wake request
    wake = wake_requests.create(phone_number="+1234567890")
    
    # List wake requests
    wakes = wake_requests.list()
""",
)

sms = _LazyAPI(
    "sms",
    """
Static access to SMS management functionality.

Provides methods for sending, receiving, and managing SMS messages.
This is a static wrapper around the SMSApi class that uses the globally
configured TextVerified instance.

Example:
    from textverified import sms
    
    # Get SMS messages
    messages = sms.list()
    
    # Get specific SMS
    message = sms.get(message_id)
""",
)


# Available for import:
__all__ = [
    # Main classes
    "TextVerified",
    "BearerToken",
    "PaginatedList",
    "TextVerifiedError",
    # Configuration
    "configure",
    # Static API access
    "account",
    "billing_cycles",
    "reservations",
    "sales",
    "services",
    "verifications",
    "wake_requests",
    "sms",
    # API classes (for direct instantiation if needed)
    "AccountAPI",
    "BillingCycleAPI",
    "ReservationsAPI",
    "SalesAPI",
    "ServicesAPI",
    "SMSApi",
    "VerificationsAPI",
    "WakeAPI",
] + data.__all__
