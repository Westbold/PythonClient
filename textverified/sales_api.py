from .action import _ActionPerformer, _Action
from typing import List
from .dtypes import AreaCode, Service, Capability

class ServicesAPI:
    """API endpoints related to services."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def get_area_codes(self) -> List[AreaCode]:
        """Get area codes for services."""
        action = _Action(method="GET", href="/api/pub/v2/area-codes")
        response = self.client._perform_action(action)
        return [AreaCode(i.get("areaCode"), i.get("state")) for i in response.data]

    def get_services(self) -> List[Service]:
        """Get services."""
        action = _Action(method="GET", href="/api/pub/v2/services")
        response = self.client._perform_action(action)
        return [Service(i.get("name"), Capability.from_string(i.get("capability"))) for i in response.data]

    # Pricing endpoints in verifications and rentals