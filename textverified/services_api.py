from .action import _ActionPerformer, _Action
from typing import List
from urllib.parse import quote
from .data import (
    AreaCode,
    InventoryQuantity,
    NumberType,
    RentalDuration,
    RentalInventoryCheckRequest,
    ReservationCapability,
    ReservationType,
    Service,
    VerificationInventoryCheckRequest,
)


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

    def rental_inventory(
        self,
        data: RentalInventoryCheckRequest = None,
        *,
        duration: RentalDuration = None,
        number_type: NumberType = None,
        service_name: str = None,
        capability: ReservationCapability = None,
    ) -> InventoryQuantity:
        """Get available inventory for a rental configuration.

        ``data`` may be supplied instead of individual arguments; explicit arguments
        take precedence over its values.
        """
        data = (
            RentalInventoryCheckRequest(
                duration=duration if duration is not None else data.duration,
                number_type=number_type if number_type is not None else data.number_type,
                service_name=service_name if service_name is not None else data.service_name,
                capability=capability if capability is not None else data.capability,
            )
            if data
            else RentalInventoryCheckRequest(duration, number_type, service_name, capability)
        )
        if not all((data.duration, data.number_type, data.service_name, data.capability)):
            raise ValueError("All required fields must be provided: duration, number_type, service_name, capability.")

        response = self.client._perform_action(
            _Action(method="POST", href="/api/pub/v2/inventory/rentals"), json=data.to_api()
        )
        return InventoryQuantity.from_api(response.data)

    def verification_inventory(
        self,
        data: VerificationInventoryCheckRequest = None,
        *,
        number_type: NumberType = None,
        service_name: str = None,
        capability: ReservationCapability = None,
    ) -> InventoryQuantity:
        """Get available inventory for a verification configuration.

        ``data`` may be supplied instead of individual arguments; explicit arguments
        take precedence over its values.
        """
        data = (
            VerificationInventoryCheckRequest(
                number_type=number_type if number_type is not None else data.number_type,
                service_name=service_name if service_name is not None else data.service_name,
                capability=capability if capability is not None else data.capability,
            )
            if data
            else VerificationInventoryCheckRequest(number_type, service_name, capability)
        )
        if not all((data.number_type, data.service_name, data.capability)):
            raise ValueError("All required fields must be provided: number_type, service_name, capability.")

        response = self.client._perform_action(
            _Action(method="POST", href="/api/pub/v2/inventory/verifications"), json=data.to_api()
        )
        return InventoryQuantity.from_api(response.data)

    def services_for_domain(self, domain: str) -> List[Service]:
        """Return services mapped to a hostname or HTTP(S) URL.

        The endpoint normalizes a hostname or full URL to its registrable domain.
        The returned service objects use the target's display name as their
        ``description``.

        Args:
            domain: A hostname or complete HTTP(S) URL to look up.

        Returns:
            Matching services. An empty list indicates that no service is mapped
            to the supplied domain.
        """
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain must be a non-empty hostname or HTTP(S) URL.")

        response = self.client._perform_action(
            _Action(method="GET", href="/api/v2/services/by-domain"), params={"domain": domain.strip()}
        )
        return [
            Service.from_api(
                {
                    "serviceName": target["serviceName"],
                    "capability": target["capability"],
                    "description": target.get("customerDisplayServiceName"),
                }
            )
            for target in response.data
        ]

    def domains_for_service(self, service_name: str) -> List[str]:
        """Return normalized domains mapped to a service name.

        Args:
            service_name: The TextVerified service name to look up.

        Returns:
            Normalized domains associated with the service, or an empty list
            when no mappings exist.
        """
        if not isinstance(service_name, str) or not service_name.strip():
            raise ValueError("service_name must be a non-empty service name.")

        action = _Action(method="GET", href=f"/api/v2/services/{quote(service_name.strip(), safe='')}/domains")
        response = self.client._perform_action(action)
        return [str(domain) for domain in response.data]
