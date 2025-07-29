from .action import _ActionPerformer, _Action
from typing import List
from .generated.generated_enums import AreaCode, Service


class ServicesAPI:
    """API endpoints related to services."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def get_area_codes(self) -> List[AreaCode]:
        """Get area codes for services."""
        action = _Action(method="GET", href="/api/pub/v2/area-codes")
        response = self.client._perform_action(action)
        return [AreaCode.from_api(i) for i in response.data]

    def get_services(self) -> List[Service]:
        """Get services."""
        action = _Action(method="GET", href="/api/pub/v2/services")
        response = self.client._perform_action(action)
        return [Service.from_api(i) for i in response.data]

    # Pricing endpoints in verifications and rentals
