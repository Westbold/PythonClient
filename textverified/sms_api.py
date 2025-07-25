from .action import _ActionPerformer, _Action
from typing import List, Union
from .generated.generated_enums import (
    Sms, NonrenewableRentalCompact, NonrenewableRentalExpanded,
    RenewableRentalCompact, RenewableRentalExpanded,
    VerificationCompact, VerificationExpanded,
    ReservationType
)
from .paginated_list import PaginatedList

class SMSApi:
    """API endpoints related to SMS"""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def list_sms(self, data: Union[NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded] = None, *, to_number: str = None, reservation_type: ReservationType = None) -> PaginatedList[Sms]:
        """List SMS messages for a specific rental or verification."""
        
        # Extract needed data from provided objects
        reservation_id = None
        if data:
            if data.number and to_number:
                raise ValueError("Cannot specify both rental/verification data and to_number.")
            to_number = data.number
        
            if isinstance(data, (NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded)):
                reservation_id = data.id

            if reservation_type is not None:
                raise ValueError("Cannot specify reservation_type when using a rental or verification object.")

        # Construct url params
        params = dict()
        if to_number:
            params['to'] = to_number

        if reservation_id:
            params['reservation_id'] = reservation_id

        if isinstance(reservation_type, ReservationType):
            params['reservation_type'] = reservation_type.to_api()

        # Construct and perform the action
        action = _Action(method="GET", href="/api/pub/v2/sms", params=params)
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data,
            parse_item=Sms.from_api,
            api_context=self.client
        )
