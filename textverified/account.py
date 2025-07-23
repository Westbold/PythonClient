from .action import _ActionPerformer

class AccountAPI:
    """API endpoints related to account management."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def get_details(self):
        """Get account details."""
        # Implementation here - you can access:
        # self.client.api_key
        # self.client.base_url
        # self.client.perform_action(action)
        pass
    
    def update_account(self, **kwargs):
        """Update account information."""
        pass