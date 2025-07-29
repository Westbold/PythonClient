from .action import _ActionPerformer, _Action
from typing import List
from .generated.generated_enums import AreaCode, Service


class ServicesAPI:
    """API endpoints related to services and area codes.
    This includes fetching available area codes and services for rental or verification.

    Please fetch area codes and services, as we update our available area codes and services frequently.
    """

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def get_area_codes(self) -> List[AreaCode]:
        """Fetch all area codes available for rental or verification services, and their associated US state.

        Returns:
            List[AreaCode]: A list of area codes with their associated US state.
        """
        action = _Action(method="GET", href="/api/pub/v2/area-codes")
        response = self.client._perform_action(action)
        return [AreaCode.from_api(i) for i in response.data]

    def get_services(self) -> List[Service]:
        """Fetch all services available for rental or verification.

        Use 'allservices' if your desired service is not listed here.

        Returns:
            List[Service]: A list of services available for rental or verification.
        """
        action = _Action(method="GET", href="/api/pub/v2/services")
        response = self.client._perform_action(action)
        return [Service.from_api(i) for i in response.data]

    # Pricing endpoints in verifications and rentals
