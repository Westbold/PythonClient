from dataclasses import dataclass
from typing import Optional, Dict
from .action import _ActionPerformer, _Action, _ActionResponse
from .account_api import AccountAPI
from .billing_cycle_api import BillingCyclesAPI
import requests
import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

@dataclass(frozen=True)
class BearerToken:
    token: str
    expiresAt: datetime.datetime

    def __post_init__(self):
        if not isinstance(self.expiresAt, datetime.datetime):
            raise ValueError("expiresAt must be a datetime object")
        if self.expiresAt.tzinfo is None:
            raise ValueError("expiresAt must be timezone-aware (UTC)")
        
    def is_expired(self) -> bool:
        """Check if the bearer token is expired."""
        return datetime.datetime.now(datetime.timezone.utc) >= self.expiresAt 

@dataclass(frozen=False)
class TextVerified(_ActionPerformer):
    """API Context for interacting with the Textverified API."""
    api_key: str
    api_username: str
    base_url: str = "https://www.textverified.com"
    user_agent: str = "TextVerified-Python"
    
    def __post_init__(self):
        # Initialize all API categories
        self.accounts = AccountAPI(self)
        self.billing_cycles = BillingCyclesAPI(self)
        self.bearer = None
        
        # Mount session with basic retry strategy for 429 and 5xx errors
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET", "POST"],
            backoff_factor=1, # 1, 2, 4s 
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def refresh_bearer(self):
        """Refresh the bearer token, if expired. Called automatically before performing actions."""
        if self.bearer is None or self.bearer.is_expired():
            response = self.session.post(
                f"{self.base_url}/api/pub/v2/auth",
                headers={
                    "X-API-KEY": f"{self.api_key}",
                    "X-API-USERNAME": f"{self.api_username}"
                }
            )
            response.raise_for_status()
            data = response.json()
            self.bearer = BearerToken(
                token=data["token"],
                expiresAt=datetime.datetime.fromisoformat(data["expiresAt"])
            )

    def _perform_action(self, action: _Action) -> _ActionResponse:
        """
        Perform an API action and return the result.
        :param action: The action to perform
        :return: Dictionary containing the API response
        """
        # Check if bearer token is set and valid
        self.refresh_bearer()
        
        # Prepare and perform the request
        headers = {
            "Authorization": f"Bearer {self.bearer.token}",
            "User-Agent": self.user_agent
        }

        response = self.session.request(
            method=action.method,
            url=f"{self.base_url}{action.href}",
            headers=headers
        )
        
        response.raise_for_status()
        return _ActionResponse(
            data=response.json(),
            headers=response.headers
        )
