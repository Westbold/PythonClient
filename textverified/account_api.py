from .action import _Action, _ActionPerformer
from dataclasses import dataclass

@dataclass(frozen=True)
class AccountDetails:
    """A snapshot of account details."""
    username: str
    current_balance: float

class AccountAPI:
    """API endpoints related to account management."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def get_details(self):
        """Get account details."""
        action = _Action(method="GET", href="/api/pub/v2/account/me")
        response = self.client._perform_action(action)
        return AccountDetails(username=response.get("username"), current_balance=response.get("currentBalance"))

    @property
    def balance(self) -> float:
        """Get the current account balance."""
        details = self.get_details()
        return details.current_balance
    
    @property
    def username(self) -> str:
        """Get the account username."""
        # Realistically, this is the only request we could cache
        details = self.get_details()
        return details.username