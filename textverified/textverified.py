from dataclasses import dataclass
from typing import Optional, Dict
from .action import _ActionPerformer, _Action
from .account import AccountAPI
from .billing_cycles import BillingCyclesAPI

@dataclass(frozen=True)
class InternalLink:
    href: str
    method: str

@dataclass(frozen=False)
class TextVerified(_ActionPerformer):
    """API Context for interacting with the Textverified API."""
    api_key: str
    base_url: str = "https://www.textverified.com"
    
    def __post_init__(self):
        # Initialize all API categories
        
        
        self.accounts = AccountAPI(self)
        self.billing_cycles = BillingCyclesAPI(self)
    
    def _perform_action(self, action: _Action) -> Dict:
        """
        Perform an API action and return the result.
        :param action: The action to perform
        :return: Dictionary containing the API response
        """
        return {}
