from .action import _ActionPerformer

class BillingCyclesAPI:
    """API endpoints related to billing cycles."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def get_billing_cycles(self):
        """Get billing cycles information."""
        # Implementation here - you can access:
        # self.client.api_key
        # self.client.base_url
        # self.client.perform_action(action)
        pass
    
    def get_current_cycle(self):
        """Get current billing cycle."""
        pass
    
    def get_cycle_usage(self, cycle_id: str):
        """Get usage for a specific billing cycle."""
        pass
