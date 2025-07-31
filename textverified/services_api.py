from .action import _ActionPerformer, _Action
from typing import List
from .data import AreaCode, Service, NumberType, ReservationType


class ServicesAPI:
    """API endpoints related to services and area codes.
    This includes fetching available area codes and services for rental or verification.

    Please fetch area codes and services, as we update our available area codes and services frequently.
    """

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def area_codes(self) -> List[AreaCode]:
        """Fetch all area codes available for rental or verification services, and their associated US state.

        Returns:
            List[AreaCode]: A list of area codes with their associated US state.
        """
        action = _Action(method="GET", href="/api/pub/v2/area-codes")
        response = self.client._perform_action(action)
        return [AreaCode.from_api(i) for i in response.data]

    def list(self, number_type: NumberType, reservation_type: ReservationType) -> List[Service]:
        """Fetch all services available for rental or verification.

        Special cases: Use 'allservices' (rentals) or 'servicenotlisted' (verifications), note that 'servicenotlisted'
        only receives sms from services that are not listed by us.

        Args:
            number_type (NumberType): The type of number. Most frequently NumberType.MOBILE.
            reservation_type (ReservationType): The type of reservation (e.g., renewable, nonrenewable, verification).
        Returns:
            List[Service]: A list of services available for rental or verification.
        """
        action = _Action(method="GET", href="/api/pub/v2/services")
        response = self.client._perform_action(
            action,
            params={
                "numberType": number_type.value if number_type else None,
                "reservationType": reservation_type.value,
            },
        )
        return [Service.from_api(i) for i in response.data]

    # Pricing endpoints in verifications and rentals
