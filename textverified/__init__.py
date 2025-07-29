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

# Import generated enums
from .generated.generated_enums import *

# Configurable, lazy-initialized static instance
_static_instance: Optional[TextVerified] = None


def _get_static_instance() -> TextVerified:
    """Get or create the static TextVerified instance."""
    global _static_instance
    if _static_instance is None:
        api_key = os.environ.get("TEXTVERIFIED_API_KEY")
        api_username = os.environ.get("TEXTVERIFIED_API_USERNAME")

        if not api_key or not api_username:
            raise ValueError(
                "TextVerified static instance not configured. "
                "Either call configure() or set TEXTVERIFIED_API_KEY and TEXTVERIFIED_API_USERNAME environment variables."
            )

        _static_instance = TextVerified(api_key=api_key, api_username=api_username)

    return _static_instance


def configure(api_key: str, api_username: str, base_url: str = "https://www.textverified.com") -> None:
    """Configure the static TextVerified instance."""
    global _static_instance
    _static_instance = TextVerified(api_key=api_key, api_username=api_username, base_url=base_url)


# Lazy access to static instance
accounts = lambda: _get_static_instance().accounts
billing_cycles = lambda: _get_static_instance().billing_cycles
reservations = lambda: _get_static_instance().reservations
sales = lambda: _get_static_instance().sales
services = lambda: _get_static_instance().services
verifications = lambda: _get_static_instance().verifications
wake_requests = lambda: _get_static_instance().wake_requests
sms = lambda: _get_static_instance().sms

# Available for import:
__all__ = [
    # Main classes
    "TextVerified",
    "BearerToken",
    "PaginatedList",
    # Configuration
    "configure",
    # Static API access
    "accounts",
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
]
