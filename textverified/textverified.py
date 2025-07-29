from dataclasses import dataclass
from typing import Optional, Dict
from .action import _ActionPerformer, _Action, _ActionResponse
from .account_api import AccountAPI
from .billing_cycle_api import BillingCycleAPI
from .reservations_api import ReservationsAPI
from .sales_api import SalesAPI
from .services_api import ServicesAPI
from .sms_api import SMSApi
from .verifications_api import VerificationsAPI
from .wake_api import WakeAPI
import requests
import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class BearerToken:
    token: str
    expires_at: datetime.datetime

    def __post_init__(self):
        if not isinstance(self.expires_at, datetime.datetime):
            raise ValueError("expires_at must be a datetime object")
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware (UTC)")

    def is_expired(self) -> bool:
        """Check if the bearer token is expired."""
        return datetime.datetime.now(datetime.timezone.utc) >= self.expires_at


@dataclass(frozen=False)
class TextVerified(_ActionPerformer):
    """API Context for interacting with the Textverified API."""

    api_key: str
    api_username: str
    base_url: str = "https://www.textverified.com"
    user_agent: str = "TextVerified-Python"

    @property
    def accounts(self) -> AccountAPI:
        return AccountAPI(self)

    @property
    def billing_cycles(self) -> BillingCycleAPI:
        return BillingCycleAPI(self)

    @property
    def reservations(self) -> ReservationsAPI:
        return ReservationsAPI(self)

    @property
    def sales(self) -> SalesAPI:
        return SalesAPI(self)

    @property
    def services(self) -> ServicesAPI:
        return ServicesAPI(self)

    @property
    def verifications(self) -> VerificationsAPI:
        return VerificationsAPI(self)

    @property
    def wake_requests(self) -> WakeAPI:
        return WakeAPI(self)

    @property
    def sms(self) -> SMSApi:
        return SMSApi(self)

    def __post_init__(self):
        self.bearer = None

        # Mount session with basic retry strategy for 429 and 5xx errors
        self.session = requests.Session()

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,  # 1, 2, 4s
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def refresh_bearer(self):
        """Refresh the bearer token, if expired. Called automatically before performing actions."""
        if self.bearer is None or self.bearer.is_expired():
            response = self.session.post(
                f"{self.base_url}/api/pub/v2/auth",
                headers={"X-API-KEY": f"{self.api_key}", "X-API-USERNAME": f"{self.api_username}"},
            )
            response.raise_for_status()
            data = response.json()
            self.bearer = BearerToken(
                token=data["token"], expires_at=datetime.datetime.fromisoformat(data["expiresAt"])
            )

    def _perform_action(self, action: _Action, **kwargs) -> _ActionResponse:
        """
        Perform an API action and return the result.
        :param action: The action to perform
        :return: Dictionary containing the API response
        """
        if "://" in action.href:
            return self.__perform_action_external(action.method, action.href, **kwargs)
        else:
            return self.__perform_action_internal(action.method, f"{self.base_url}{action.href}", **kwargs)

    def __perform_action_internal(self, method: str, href: str, **kwargs) -> _ActionResponse:
        """Internal action performance with authorization"""
        # Check if bearer token is set and valid
        self.refresh_bearer()

        # Prepare and perform the request
        headers = {"Authorization": f"Bearer {self.bearer.token}", "User-Agent": self.user_agent}

        response = self.session.request(method=method, url=href, headers=headers, **kwargs)

        response.raise_for_status()
        return _ActionResponse(data=response.json(), headers=response.headers)

    def __perform_action_external(self, method: str, href: str, **kwargs) -> _ActionResponse:
        """External action performance without authorization"""
        response = self.session.request(method=method, url=href, headers={"User-Agent": self.user_agent}, **kwargs)

        response.raise_for_status()
        return _ActionResponse(data=response.json(), headers=response.headers)
