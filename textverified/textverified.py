from dataclasses import dataclass
from typing import Optional, Dict
from .action import _ActionPerformer, _Action, _ActionResponse
from .account_api import AccountAPI
from .billing_cycle_api import BillingCycleAPI
from .exceptions import TextVerifiedError
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
import dateutil.parser
from http.client import responses


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
    user_agent: str = "TextVerified-Python-Client/0.1.0"

    @property
    def account(self) -> AccountAPI:
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
        self.base_url = self.base_url.rstrip("/")

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
            verify = not self.base_url.startswith("http://localhost") and not self.base_url.startswith(
                "https://localhost"
            )

            response = self.session.post(
                f"{self.base_url}/api/pub/v2/auth",
                headers={"X-API-KEY": f"{self.api_key}", "X-API-USERNAME": f"{self.api_username}"},
                verify=verify,
            )
            TextVerified.__raise_for_status("POST", f"{self.base_url}/api/pub/v2/auth", response)
            data = response.json()
            self.bearer = BearerToken(token=data["token"], expires_at=dateutil.parser.parse(data["expiresAt"]))

    def _perform_action(self, action: _Action, **kwargs) -> _ActionResponse:
        """
        Perform an API action and return the result.
        :param action: The action to perform
        :return: Dictionary containing the API response
        """
        if "://" in action.href and not action.href.startswith(self.base_url):
            return self.__perform_action_external(action.method, action.href, **kwargs)
        else:
            href = action.href
            if not action.href.startswith(self.base_url):
                href = f"{self.base_url}{action.href}"
            return self.__perform_action_internal(action.method, href, **kwargs)

    def __perform_action_internal(self, method: str, href: str, **kwargs) -> _ActionResponse:
        """Internal action performance with authorization"""
        # Check if bearer token is set and valid
        self.refresh_bearer()

        # Prepare and perform the request
        headers = {"Authorization": f"Bearer {self.bearer.token}", "User-Agent": self.user_agent}

        # Allow unverified certificates for localhost
        verify = not href.startswith("http://localhost") and not href.startswith("https://localhost")

        response = self.session.request(method=method, url=href, headers=headers, verify=verify, **kwargs)

        TextVerified.__raise_for_status(method, href, response)
        return _ActionResponse(data=response.json() if response.text else {}, headers=response.headers)

    def __perform_action_external(self, method: str, href: str, **kwargs) -> _ActionResponse:
        """External action performance without authorization"""
        # Allow unverified certificates for localhost
        verify = not href.startswith("http://localhost") and not href.startswith("https://localhost")

        response = self.session.request(
            method=method, url=href, headers={"User-Agent": self.user_agent}, verify=verify, **kwargs
        )

        TextVerified.__raise_for_status(method, href, response)
        return _ActionResponse(data=response.json() if response.text else {}, headers=response.headers)

    @classmethod
    def __raise_for_status(cls, method: str, href: str, response: requests.Response):
        """Raise an exception for HTTP errors."""
        if response.status_code > 299 or response.status_code < 200:
            http_error_text = f"HTTP {response.status_code} ({responses[response.status_code]}) for {method} {href}"
            try:
                error_data = response.json()
                raise TextVerifiedError(
                    error_code=error_data.get("errorCode"),
                    error_description=error_data.get("errorDescription"),
                    context=http_error_text,
                )
            except ValueError:
                error_text = response.text
            raise requests.HTTPError(f"{http_error_text}:\n{error_text}")
