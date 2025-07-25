from .action import _ActionPerformer, _Action
from typing import List, Union
from .paginated_list import PaginatedList
from .generated.generated_enums import (
    VerificationPriceCheckRequest, NewVerificationRequest,
    PricingSnapshot, ReservationCapability, NumberType
)

class VerificationsAPI:
    """API endpoints related to verifications."""

    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def create_verification(self, data: NewVerificationRequest = None, *,
        area_code_select_option: List[str]
        carrier_select_option: List[str]
        service_name: str
        capability: ReservationCapability
        service_not_listed_name: str
        max_price: float
    ) -> VerificationExpanded:
        """Creates a new verification."""

        data = NewVerificationRequest(
            area_code_select_option=area_code_select_option if area_code_select_option is not None else data.area_code_select_option,
            carrier_select_option=carrier_select_option if carrier_select_option is not None else data.carrier_select_option,
            service_name=service_name or data.service_name,
            capability=capability or data.capability,
            service_not_listed_name=data.service_not_listed_name,
            max_price=max_price if max_price is not None else data.max_price
        )

        if not data or not data.service_name or not data.capability:
            raise ValueError("All required fields must be provided: service_name and capability.")

        action = _Action(method="POST", href="/api/pub/v2/verifications")
        response = self.client._perform_action(action, json=data)

        # Note - response.data is another action to follow to get Verification details
        
        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return VerificationExpanded.from_api(response.data)


    def get_verification_pricing(self, data: Union[NewVerificationRequest, VerificationPriceCheckRequest] = None, *,
        service_name: str = None,
        area_code: bool = None,
        carrier: bool = None,
        number_type: NumberType = None,
        capability: ReservationCapability = None
    ) -> PricingSnapshot:
        """Get pricing for a verification."""
        
        # Convert NewVerificationRequest to VerificationPriceCheckRequest if needed
        if isinstance(data, NewVerificationRequest):
            data = VerificationPriceCheckRequest(
                service_name=data.service_name,
                area_code=True if data.area_code_select_option else None,
                carrier=True if data.carrier_select_option else None,
                number_type=NumberType.VOIP if data.capability == ReservationCapability.VOICE else NumberType.MOBILE,
                capability=data.capability
            )

        data = VerificationPriceCheckRequest(
            service_name=service_name or data.service_name,
            area_code=area_code if area_code is not None else data.area_code,
            carrier=carrier if carrier is not None else data.carrier,
            number_type=number_type or data.number_type,
            capability=capability or data.capability
        ) if data else VerificationPriceCheckRequest(
            service_name=service_name,
            area_code=area_code,
            carrier=carrier,
            number_type=number_type,
            capability=capability
        )

        if not data or not data.service_name or not data.area_code or not data.carrier or not data.number_type or not data.capability:
            raise ValueError("All required fields must be provided: service_name, area_code, carrier, number_type, and capability.")

        action = _Action(method="POST", href="/api/pub/v2/pricing/verifications")
        response = self.client._perform_action(action, json=data)

        return PricingSnapshot.from_api(response.data)

    def get_verification_details(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> VerificationExpanded:
        """Get details for a specific verification."""
        
        verification_id = verification_id.id if isinstance(verification_id, (VerificationCompact, VerificationExpanded)) else verification_id

        if not verification_id:
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/verifications/{verification_id}")
        response = self.client._perform_action(action)

        return VerificationExpanded.from_api(response.data)

    def get_verifications(self) -> PaginatedList[VerificationCompact]:
        """Get a list of verifications."""
        
        action = _Action(method="GET", href="/api/pub/v2/verifications")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data,
            parse_item=VerificationCompact.from_api,
            api_context=self.client
        )


    def cancel_reservation(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Cancel a verification."""
        
        verification_id = verification_id.id if isinstance(verification_id, (VerificationCompact, VerificationExpanded)) else verification_id

        if not verification_id:
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/cancel")
        response = self.client._perform_action(action)

        return True

    def reactivate_verification(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Reactivate a verification."""
        
        # TODO: If the verification ID CAN change, return a new VerificationXXX instance (depending on what the API return action is)
        # Otherwise, leave as bool (can't change ID)

        verification_id = verification_id.id if isinstance(verification_id, (VerificationCompact, VerificationExpanded)) else verification_id

        if not verification_id:
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/reactivate")
        response = self.client._perform_action(action)

        return True

    def reuse_verification(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Reuse a verification."""
        
        # TODO: If the verification ID CAN change, return a new VerificationXXX instance (depending on what the API return action is)
        # Otherwise, leave as bool (can't change ID)

        verification_id = verification_id.id if isinstance(verification_id, (VerificationCompact, VerificationExpanded)) else verification_id

        if not verification_id:
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/reuse")
        response = self.client._perform_action(action)

        return True

    def report_verification(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Report a verification."""
        
        verification_id = verification_id.id if isinstance(verification_id, (VerificationCompact, VerificationExpanded)) else verification_id

        if not verification_id:
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/report")
        response = self.client._perform_action(action)

        return True