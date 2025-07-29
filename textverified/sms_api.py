from .action import _ActionPerformer, _Action
from typing import List, Union, Iterator
from .generated.generated_enums import (
    Sms, NonrenewableRentalCompact, NonrenewableRentalExpanded,
    RenewableRentalCompact, RenewableRentalExpanded,
    VerificationCompact, VerificationExpanded,
    ReservationType
)
from .paginated_list import PaginatedList
import time
import datetime

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
        action = _Action(method="GET", href="/api/pub/v2/sms")
        response = self.client._perform_action(action, params=params)

        return PaginatedList(
            request_json=response.data,
            parse_item=Sms.from_api,
            api_context=self.client
        )
        
    def incoming_sms(self, data: Union[NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded] = None, *, to_number: str = None, reservation_type: ReservationType = None, timeout: float = 10.0, polling_interval: float = 1.0) -> Iterator[Sms]:
        """Iterator over future incoming sms"""
        earliest_msg = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=3) # allow some leniency
        start_time = time.monotonic()

        already_seen = set()
        
        # wait up to [timeout] seconds for a NEW message
        while time.monotonic() - start_time < timeout:
            time.sleep(polling_interval)  # Polling interval
            new_messages = self.list_sms(data=data, to_number=to_number, reservation_type=reservation_type)
            for msg in new_messages:
                if msg.id not in already_seen and msg.created_at > earliest_msg:
                    already_seen.add(msg.id)
                    yield msg
