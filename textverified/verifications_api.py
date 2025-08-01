from .action import _ActionPerformer, _Action
from typing import List, Union
from .paginated_list import PaginatedList
from .data import (
    VerificationPriceCheckRequest,
    NewVerificationRequest,
    PricingSnapshot,
    ReservationCapability,
    NumberType,
    VerificationCompact,
    VerificationExpanded,
)


class VerificationsAPI:
    """API endpoints related to verifications."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def create(
        self,
        data: NewVerificationRequest = None,
        *,
        area_code_select_option: List[str] = None,
        carrier_select_option: List[str] = None,
        service_name: str = None,
        capability: ReservationCapability = None,
        service_not_listed_name: str = None,
        max_price: float = None,
    ) -> VerificationExpanded:
        """Create a new verification for phone number verification purposes.

        Verifications are used to receive SMS or voice calls for account verification on various services.
        This will cost API balance, so ensure you have sufficient funds before calling this method.
        To estimate the cost, use `get_verification_pricing()` with the same parameters.

        Args:
            data (NewVerificationRequest, optional): The verification details to create. All kwargs will overwrite values in this object. Defaults to None.
            area_code_select_option (List[str], optional): List of preferred area codes for the verification number. Defaults to None.
            carrier_select_option (List[str], optional): List of preferred carriers for the verification number. Defaults to None.
            service_name (str, optional): Name of the service requiring verification. Can be found by calling `textverified.services.get_services()`. Defaults to None.
            capability (ReservationCapability, optional): The capabilities required (voice, sms, or both) for this verification. Defaults to None.
            service_not_listed_name (str, optional): Custom service name if the service is not listed in available services. Defaults to None.
            max_price (float, optional): Maximum price you're willing to pay for this verification. Defaults to None.

        Raises:
            ValueError: If required fields service_name and capability are not provided.

        Returns:
            VerificationExpanded: The details of the created verification.
        """

        data = (
            NewVerificationRequest(
                area_code_select_option=(
                    area_code_select_option if area_code_select_option is not None else data.area_code_select_option
                ),
                carrier_select_option=(
                    carrier_select_option if carrier_select_option is not None else data.carrier_select_option
                ),
                service_name=service_name or data.service_name,
                capability=capability or data.capability,
                service_not_listed_name=(
                    service_not_listed_name if service_not_listed_name is not None else data.service_not_listed_name
                ),
                max_price=max_price if max_price is not None else data.max_price,
            )
            if data
            else NewVerificationRequest(
                area_code_select_option=area_code_select_option,
                carrier_select_option=carrier_select_option,
                service_name=service_name,
                capability=capability,
                service_not_listed_name=service_not_listed_name,
                max_price=max_price,
            )
        )

        if not data or not data.service_name or not data.capability:
            raise ValueError("All required fields must be provided: service_name and capability.")

        if data.service_name == "allservices":
            raise ValueError(
                "Allservices is not supported for verifications. Please use a specific service name, or 'servicenotlisted'/'servicenotlistedvoice'."
            )

        action = _Action(method="POST", href="/api/pub/v2/verifications")
        response = self.client._perform_action(action, json=data.to_api())

        # Note - response.data is another action to follow to get Verification details

        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return VerificationExpanded.from_api(response.data)

    def pricing(
        self,
        data: Union[NewVerificationRequest, VerificationPriceCheckRequest] = None,
        *,
        service_name: str = None,
        area_code: bool = None,
        carrier: bool = None,
        number_type: NumberType = None,
        capability: ReservationCapability = None,
    ) -> PricingSnapshot:
        """Get pricing information for a verification before creating it.

        This method allows you to check the cost of a verification before purchasing it.
        You can pass the a NewVerificationRequest to verify the pricing for that specific configuration before creating it,
        or provide individual parameters to check pricing for a specific service, area code, carrier, number type, and capability.

        Args:
            data (Union[NewVerificationRequest, VerificationPriceCheckRequest], optional): The verification details to price. All kwargs will overwrite values in this object. Defaults to None.
            service_name (str, optional): Name of the service requiring verification. Defaults to None.
            area_code (bool, optional): Whether to request a specific area code. Defaults to None.
            carrier (bool, optional): Whether to request a specific carrier. Defaults to None.
            number_type (NumberType, optional): The underlying type of the number (mobile, voip, etc.). Defaults to None.
            capability (ReservationCapability, optional): The capabilities required (voice, sms, or both) for this verification. Defaults to None.

        Raises:
            ValueError: If any required fields are missing or invalid.

        Returns:
            PricingSnapshot: The pricing information for the requested verification configuration.
        """

        # Convert NewVerificationRequest to VerificationPriceCheckRequest if needed
        if isinstance(data, NewVerificationRequest):
            data = VerificationPriceCheckRequest(
                service_name=data.service_name,
                capability=data.capability,
                area_code=True if data.area_code_select_option else False,
                carrier=True if data.carrier_select_option else False,
                number_type=NumberType.VOIP if data.capability == ReservationCapability.VOICE else NumberType.MOBILE,
            )

        data = (
            VerificationPriceCheckRequest(
                service_name=service_name or data.service_name,
                area_code=area_code if area_code is not None else data.area_code,
                carrier=carrier if carrier is not None else data.carrier,
                number_type=number_type or data.number_type,
                capability=capability or data.capability,
            )
            if data
            else VerificationPriceCheckRequest(
                service_name=service_name,
                area_code=area_code,
                carrier=carrier,
                number_type=number_type,
                capability=capability,
            )
        )

        if (
            data is None
            or data.service_name is None
            or data.area_code is None
            or data.carrier is None
            or data.number_type is None
            or data.capability is None
        ):
            raise ValueError(
                "All required fields must be provided: service_name, area_code, carrier, number_type, and capability."
            )

        action = _Action(method="POST", href="/api/pub/v2/pricing/verifications")
        response = self.client._perform_action(action, json=data.to_api())

        return PricingSnapshot.from_api(response.data)

    def details(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> VerificationExpanded:
        """Get detailed information about a verification by ID.

        Args:
            verification_id (Union[str, VerificationCompact, VerificationExpanded]): The ID or instance of the verification to retrieve.

        Raises:
            ValueError: If verification_id is not a valid ID or instance.

        Returns:
            VerificationExpanded: The detailed information about the verification.
        """

        verification_id = (
            verification_id.id
            if isinstance(verification_id, (VerificationCompact, VerificationExpanded))
            else verification_id
        )

        if not verification_id or not isinstance(verification_id, str):
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/verifications/{verification_id}")
        response = self.client._perform_action(action)

        return VerificationExpanded.from_api(response.data)

    def list(self) -> PaginatedList[VerificationCompact]:
        """Get a paginated list of all verifications associated with this account.

        Returns:
            PaginatedList[VerificationCompact]: A paginated list of verification records.
        """

        action = _Action(method="GET", href="/api/pub/v2/verifications")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=VerificationCompact.from_api, api_context=self.client
        )

    def cancel(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Cancel an active verification.

        This will stop the verification process and may result in a refund depending on the verification status.

        Args:
            verification_id (Union[str, VerificationCompact, VerificationExpanded]): The ID or instance of the verification to cancel.

        Raises:
            ValueError: If verification_id is not a valid ID or instance.

        Returns:
            bool: True if the cancellation was successful, False otherwise.
        """

        verification_id = (
            verification_id.id
            if isinstance(verification_id, (VerificationCompact, VerificationExpanded))
            else verification_id
        )

        if not verification_id or not isinstance(verification_id, str):
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/cancel")
        response = self.client._perform_action(action)

        return True

    def reactivate(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Reactivate a previously cancelled or expired verification.

        This allows you to resume using a verification that was previously cancelled or has expired,
        making it available to receive SMS or voice calls again.

        Args:
            verification_id (Union[str, VerificationCompact, VerificationExpanded]): The ID or instance of the verification to reactivate.

        Raises:
            ValueError: If verification_id is not a valid ID or instance.

        Returns:
            bool: True if the reactivation was successful, False otherwise.
        """

        # TODO: If the verification ID CAN change, return a new VerificationXXX instance (depending on what the API return action is)
        # Otherwise, leave as bool (can't change ID)

        verification_id = (
            verification_id.id
            if isinstance(verification_id, (VerificationCompact, VerificationExpanded))
            else verification_id
        )

        if not verification_id or not isinstance(verification_id, str):
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/reactivate")
        response = self.client._perform_action(action)

        return True

    def reuse(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Reuse an existing verification for another service verification.

        This allows you to use the same verification number for multiple service verifications,
        potentially saving on costs when you need to verify accounts with multiple services.

        Args:
            verification_id (Union[str, VerificationCompact, VerificationExpanded]): The ID or instance of the verification to reuse.

        Raises:
            ValueError: If verification_id is not a valid ID or instance.

        Returns:
            bool: True if the reuse was successful, False otherwise.
        """

        # TODO: If the verification ID CAN change, return a new VerificationXXX instance (depending on what the API return action is)
        # Otherwise, leave as bool (can't change ID)

        verification_id = (
            verification_id.id
            if isinstance(verification_id, (VerificationCompact, VerificationExpanded))
            else verification_id
        )

        if not verification_id or not isinstance(verification_id, str):
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/reuse")
        response = self.client._perform_action(action)

        return True

    def report(self, verification_id: Union[str, VerificationCompact, VerificationExpanded]) -> bool:
        """Report an issue with a verification.

        Use this method to report problems with a verification, such as not receiving SMS/calls,
        number not working, or other issues. This may result in a refund or credit.

        Args:
            verification_id (Union[str, VerificationCompact, VerificationExpanded]): The ID or instance of the verification to report.

        Raises:
            ValueError: If verification_id is not a valid ID or instance.

        Returns:
            bool: True if the report was submitted successfully, False otherwise.
        """

        verification_id = (
            verification_id.id
            if isinstance(verification_id, (VerificationCompact, VerificationExpanded))
            else verification_id
        )

        if not verification_id or not isinstance(verification_id, str):
            raise ValueError("verification_id must be a valid ID or instance of VerificationCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/verifications/{verification_id}/report")
        response = self.client._perform_action(action)

        return True
