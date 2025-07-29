from .action import _ActionPerformer, _Action
from typing import List, Union
from .paginated_list import PaginatedList
from .generated.generated_enums import (
    RenewableRentalCompact,
    RenewableRentalExpanded,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    BackOrderReservationCompact,
    BackOrderReservationExpanded,
    LineHealth,
    RentalExtensionRequest,
    RentalDuration,
    NewRentalRequest,
    RentalPriceCheckRequest,
    PricingSnapshot,
    NumberType,
    ReservationCapability,
    ReservationSaleExpanded,
    RenewableRentalUpdateRequest,
    NonrenewableRentalUpdateRequest,
)


class ReservationsAPI:
    """API endpoints related to reservations."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def create_rental_reservation(
        self,
        data: NewRentalRequest = None,
        *,
        allow_back_order_reservations: bool = None,
        always_on: bool = None,
        area_code_select_option: List[str] = None,
        duration: RentalDuration = None,
        is_renewable: bool = None,
        number_type: NumberType = None,
        billing_cycle_id_to_assign_to: str = None,
        service_name: str = None,
        capability: ReservationCapability = None,
    ) -> ReservationSaleExpanded:
        """Creates a new sale"""
        data = (
            NewRentalRequest(
                allow_back_order_reservations=allow_back_order_reservations
                if allow_back_order_reservations is not None
                else data.allow_back_order_reservations,
                always_on=always_on if always_on is not None else data.always_on,
                area_code_select_option=area_code_select_option or data.area_code_select_option,
                duration=duration or data.duration,
                is_renewable=is_renewable if is_renewable is not None else data.is_renewable,
                number_type=number_type or data.number_type,
                billing_cycle_id_to_assign_to=billing_cycle_id_to_assign_to or data.billing_cycle_id_to_assign_to,
                service_name=service_name or data.service_name,
                capability=capability or data.capability,
            )
            if data
            else NewRentalRequest(
                allow_back_order_reservations=allow_back_order_reservations,
                always_on=always_on,
                area_code_select_option=area_code_select_option,
                duration=duration,
                is_renewable=is_renewable,
                number_type=number_type,
                billing_cycle_id_to_assign_to=billing_cycle_id_to_assign_to,
                service_name=service_name,
                capability=capability,
            )
        )

        if (
            not data
            or data.allow_back_order_reservations is None
            or data.always_on is None
            or data.duration is None
            or data.is_renewable is None
            or data.number_type is None
            or data.service_name is None
            or data.capability is None
        ):
            raise ValueError(
                "All required fields must be provided: allow_back_order_reservations, always_on, duration, is_renewable, number_type, service_name, capability."
            )

        action = _Action(method="POST", href="/api/pub/v2/reservations/rental")
        response = self.client._perform_action(action, json=data)

        # Note - response.data is another action to follow to get Sale details
        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return ReservationSaleExpanded.from_api(response.data)

    def get_rental_pricing(
        self,
        data: Union[NewRentalRequest, RentalPriceCheckRequest] = None,
        *,
        service_name: str = None,
        area_code: bool = None,
        number_type: NumberType = None,
        capability: ReservationCapability = None,
        always_on: bool = None,
        call_forwarding: bool = None,
        billing_cycle_id_to_assign_to: str = None,
        is_renewable: bool = None,
        duration: RentalDuration = None,
    ) -> PricingSnapshot:
        """Get rental pricing."""

        # If we are provided a NewRentalRequest, convert it to a RentalPriceCheckRequest
        if isinstance(data, NewRentalRequest):
            data = RentalPriceCheckRequest(
                service_name=data.service_name,
                area_code=bool(data.area_code_select_option),
                number_type=data.number_type,
                capability=data.capability,
                always_on=data.always_on,
                call_forwarding=False,
                billing_cycle_id_to_assign_to=data.billing_cycle_id_to_assign_to,
                is_renewable=data.is_renewable,
                duration=data.duration,
            )

        data = (
            RentalPriceCheckRequest(
                service_name=service_name or data.service_name,
                area_code=area_code if area_code is not None else data.area_code,
                number_type=number_type or data.number_type,
                capability=capability or data.capability,
                always_on=always_on if always_on is not None else data.always_on,
                call_forwarding=call_forwarding if call_forwarding is not None else data.call_forwarding,
                billing_cycle_id_to_assign_to=billing_cycle_id_to_assign_to or data.billing_cycle_id_to_assign_to,
                is_renewable=is_renewable if is_renewable is not None else data.is_renewable,
                duration=duration or data.duration,
            )
            if data
            else RentalPriceCheckRequest(
                service_name=service_name,
                area_code=area_code,
                number_type=number_type,
                capability=capability,
                always_on=always_on,
                call_forwarding=call_forwarding,
                billing_cycle_id_to_assign_to=billing_cycle_id_to_assign_to,
                is_renewable=is_renewable,
                duration=duration,
            )
        )

        if (
            not data
            or data.service_name is None
            or data.area_code is None
            or data.number_type is None
            or data.capability is None
            or data.always_on is None
            or data.is_renewable is None
            or data.duration is None
        ):
            raise ValueError(
                "All required fields must be provided: service_name, area_code, number_type, capability, always_on, is_renewable, duration."
            )

        action = _Action(method="POST", href="/api/pub/v2/pricing/rentals")
        response = self.client._perform_action(action, json=data)

        return PricingSnapshot.from_api(response.data)

    def get_backorder_reservation(
        self, reservation_id: Union[str, BackOrderReservationCompact, BackOrderReservationExpanded]
    ) -> BackOrderReservationExpanded:
        """Get backorder reservations."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (BackOrderReservationCompact, BackOrderReservationExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of BackOrderReservationCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/backorders/{reservation_id}")
        response = self.client._perform_action(action)
        return BackOrderReservationExpanded.from_api(response.data)

    def get_reservation_details(
        self,
        reservation_id: Union[
            str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded
        ],
    ) -> Union[RenewableRentalExpanded, NonrenewableRentalExpanded]:
        """Get reservation details."""
        reservation_id = (
            reservation_id.id
            if isinstance(
                reservation_id,
                (
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                ),
            )
            else reservation_id
        )

        if not reservation_id:
            raise ValueError(
                "reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded or NonrenewableRentalCompact/Expanded."
            )

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/{reservation_id}")
        response = self.client._perform_action(action)

        # Note - response.data is another action to follow

        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        if "reservations/rental/nonrenewable/" in action.href:
            return NonrenewableRentalExpanded.from_api(response.data)

        elif "reservations/rental/renewable/" in action.href:
            return RenewableRentalExpanded.from_api(response.data)

    def get_renewable_reservations(self) -> PaginatedList[RenewableRentalCompact]:
        """Get a list of renewable reservations."""
        action = _Action(method="GET", href="/api/pub/v2/reservations/rental/renewable")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=RenewableRentalCompact.from_api, api_context=self.client
        )

    def get_nonrenewable_reservations(self) -> PaginatedList[NonrenewableRentalCompact]:
        """Get a list of non-renewable reservations."""
        action = _Action(method="GET", href="/api/pub/v2/reservations/rental/nonrenewable")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=NonrenewableRentalCompact.from_api, api_context=self.client
        )

    def get_renewable_reservation_details(
        self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]
    ) -> RenewableRentalExpanded:
        """Get renewable reservation details."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}")
        response = self.client._perform_action(action)

        return RenewableRentalExpanded.from_api(response.data)

    def get_nonrenewable_reservation_details(
        self, reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]
    ) -> NonrenewableRentalExpanded:
        """Get non-renewable reservation details."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of NonrenewableRentalCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/rental/nonrenewable/{reservation_id}")
        response = self.client._perform_action(action)

        return NonrenewableRentalExpanded.from_api(response.data)

    def check_reservation_health(
        self,
        reservation_id: Union[
            str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded
        ],
    ) -> LineHealth:
        """Check the health of a reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(
                reservation_id,
                (
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                ),
            )
            else reservation_id
        )

        if not reservation_id:
            raise ValueError(
                "reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded or NonrenewableRentalCompact/Expanded."
            )

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/{reservation_id}/health")
        response = self.client._perform_action(action)

        return LineHealth.from_api(response.data)

    def update_renewable_reservation(
        self,
        reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded],
        data: RenewableRentalUpdateRequest = None,
        *,
        user_notes: str = None,
        include_for_renewal: bool = None,
        mark_all_sms_read: bool = None,
    ) -> bool:
        """Update a renewable reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        update_request = (
            RenewableRentalUpdateRequest(
                user_notes=user_notes or data.user_notes,
                include_for_renewal=include_for_renewal
                if include_for_renewal is not None
                else data.include_for_renewal,
                mark_all_sms_read=mark_all_sms_read if mark_all_sms_read is not None else data.mark_all_sms_read,
            )
            if data
            else RenewableRentalUpdateRequest(
                user_notes=user_notes, include_for_renewal=include_for_renewal, mark_all_sms_read=mark_all_sms_read
            )
        )

        if not update_request or (
            not update_request.user_notes
            and update_request.include_for_renewal is None
            and update_request.mark_all_sms_read is None
        ):
            raise ValueError(
                "At least one field must be updated: user_notes, include_for_renewal, or mark_all_sms_read."
            )

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}")
        response = self.client._perform_action(action, json=update_request.to_api())

        return True

    # Possibility for unified update method?

    def update_nonrenewable_reservation(
        self,
        reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded],
        data: NonrenewableRentalUpdateRequest = None,
        *,
        user_notes: str = None,
        mark_all_sms_read: bool = None,
    ) -> bool:
        """Update a non-renewable reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of NonrenewableRentalCompact/Expanded.")

        update_request = (
            NonrenewableRentalUpdateRequest(
                user_notes=user_notes or data.user_notes,
                mark_all_sms_read=mark_all_sms_read if mark_all_sms_read is not None else data.mark_all_sms_read,
            )
            if data
            else NonrenewableRentalUpdateRequest(user_notes=user_notes, mark_all_sms_read=mark_all_sms_read)
        )

        if not update_request or (not update_request.user_notes and update_request.mark_all_sms_read is None):
            raise ValueError("At least one field must be updated: user_notes or mark_all_sms_read.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/nonrenewable/{reservation_id}")
        response = self.client._perform_action(action, json=update_request.to_api())

        return True

    def refund_renewable_reservation(
        self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]
    ) -> bool:
        """Refund a renewable reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}/refund")
        self.client._perform_action(action)

        return True

    def refund_nonrenewable_reservation(
        self, reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]
    ) -> bool:
        """Refund a non-renewable reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of NonrenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/nonrenewable/{reservation_id}/refund")
        self.client._perform_action(action)

        return True

    def renew_overdue_renewable_reservation(
        self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]
    ) -> bool:
        """Renew an overdue renewable reservation."""
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}/renew")
        self.client._perform_action(action)

        return True

    def extend_nonrenewable_reservation(
        self,
        data: RentalExtensionRequest = None,
        *,
        extension_duration: RentalDuration = None,
        rental_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded] = None,
    ) -> bool:
        """Extend a non-renewable reservation."""
        data = (
            RentalExtensionRequest(
                extension_duration=extension_duration or data.extension_duration, rental_id=rental_id or data.rental_id
            )
            if data
            else RentalExtensionRequest(extension_duration=extension_duration, rental_id=rental_id)
        )

        if not data or not data.extension_duration or not data.rental_id:
            raise ValueError("Both extension_duration and rental_id must be provided.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rentals/extensions")
        self.client._perform_action(action, json=data.to_api())

        return True
