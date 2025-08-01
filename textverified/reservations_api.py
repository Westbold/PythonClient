from .action import _ActionPerformer, _Action
from typing import List, Union
from .paginated_list import PaginatedList
from .data import (
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
    Reservation,
    ReservationCapability,
    ReservationSaleExpanded,
    RenewableRentalUpdateRequest,
    NonrenewableRentalUpdateRequest,
)


class ReservationsAPI:
    """API endpoints related to reservations.
    This includes both renewable and non-renewable rentals, as well as backorder reservations.

    Note that reservations which are not always-on require a wakeup to receive sms. To wake a resrvation, use `textverified.wake_requests.create_wake_request(...)`.
    """

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def create(
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
        """Purchase a new rental. Returns a ReservationSaleExpanded, which contains a list of reservations and backorder reservations.
        You will need to call `.details(obj)` on each reservation to get its full details.

        `service_name` can be found by calling `textverified.ServiceAPI.get_services()`.

        This will cost api balance, so ensure you have sufficient funds before calling this method.
        To estimate the cost, use `get_rental_pricing()` with the same parameters. You can pass the same NewRentalRequest object to both methods.

        Args:
            data (NewRentalRequest, optional): The rental details to create. All kwargs will overwrite values in this object. Defaults to None.
            allow_back_order_reservations (bool, optional): If true, a rental back order will be created if the requested rental is out of stock. Defaults to None.
            always_on (bool, optional): If set to true, a line that does not require wake up will be assigned if in stock. Otherwise, wakeup will be required. Defaults to None.
            area_code_select_option (List[str], optional): List of allowed area codes. Defaults to None.
            duration (RentalDuration, optional): Requested duration of the rental. Defaults to None.
            is_renewable (bool, optional): Whether the rental is renewable. Defaults to None.
            number_type (NumberType, optional): The underlying type of the number. Defaults to None.
            billing_cycle_id_to_assign_to (str, optional): Optional billing cycle to which the rental is assigned. If left empty, a new billing cycle will be created for the rental. Only renewable rentals can be assigned to a billing cycle. Defaults to None.
            service_name (str, optional): Name of the service. Defaults to None.
            capability (ReservationCapability, optional): The capabilities (voice, sms, or both) of this rental. Defaults to None.

        Raises:
            ValueError: If any required fields are missing or invalid.

        Returns:
            ReservationSaleExpanded: The details of the created rental reservation.
        """
        data = (
            NewRentalRequest(
                allow_back_order_reservations=(
                    allow_back_order_reservations
                    if allow_back_order_reservations is not None
                    else data.allow_back_order_reservations
                ),
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
            data is None
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
        response = self.client._perform_action(action, json=data.to_api())

        # Note - response.data is another action to follow to get Sale details
        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return ReservationSaleExpanded.from_api(response.data)

    def pricing(
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
        """Get rental pricing information for a potential rental reservation.

        This method allows you to check the cost of a rental before purchasing it.
        You can pass the a NewRentalRequest to verify the pricing for that specific configuration before creating it,
        or provide individual parameters to check pricing for a specific service, area code, capability, or number type.

        Args:
            data (Union[NewRentalRequest, RentalPriceCheckRequest], optional): The rental details to price. All kwargs will overwrite values in this object. Defaults to None.
            service_name (str, optional): Name of the service. Defaults to None.
            area_code (bool, optional): Whether to request a specific area code. Defaults to None.
            number_type (NumberType, optional): The underlying type of the number. Defaults to None.
            capability (ReservationCapability, optional): The capabilities (voice, sms, or both) of this rental. Defaults to None.
            always_on (bool, optional): If set to true, a line that does not require wake up will be assigned if in stock. Defaults to None.
            call_forwarding (bool, optional): Whether call forwarding is enabled. Defaults to None.
            billing_cycle_id_to_assign_to (str, optional): Optional billing cycle to which the rental would be assigned. Defaults to None.
            is_renewable (bool, optional): Whether the rental is renewable. Defaults to None.
            duration (RentalDuration, optional): Requested duration of the rental. Defaults to None.

        Raises:
            ValueError: If any required fields are missing or invalid.

        Returns:
            PricingSnapshot: The pricing information for the requested rental configuration.
        """

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

    def backorder(
        self, reservation_id: Union[str, BackOrderReservationCompact, BackOrderReservationExpanded]
    ) -> BackOrderReservationExpanded:
        """Get details of a backorder reservation by ID.

        Args:
            reservation_id (Union[str, BackOrderReservationCompact, BackOrderReservationExpanded]): The ID or instance of the backorder reservation to retrieve.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            BackOrderReservationExpanded: The detailed information about the backorder reservation.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (BackOrderReservationCompact, BackOrderReservationExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of BackOrderReservationCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/backorders/{reservation_id}")
        response = self.client._perform_action(action)
        return BackOrderReservationExpanded.from_api(response.data)

    def details(
        self,
        reservation_id: Union[
            str,
            Reservation,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
        ],
    ) -> Union[RenewableRentalExpanded, NonrenewableRentalExpanded]:
        """Get detailed information about a reservation (renewable or non-renewable).

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the reservation to retrieve.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            Union[RenewableRentalExpanded, NonrenewableRentalExpanded]: The detailed information about the reservation. Type depends on whether the reservation is renewable or not.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(
                reservation_id,
                (
                    Reservation,
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                ),
            )
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of Reservation.")

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/{reservation_id}")
        response = self.client._perform_action(action)

        # Note - response.data is another action to follow

        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        if "reservations/rental/nonrenewable/" in action.href:
            return NonrenewableRentalExpanded.from_api(response.data)

        elif "reservations/rental/renewable/" in action.href:
            return RenewableRentalExpanded.from_api(response.data)

    def list_renewable(self) -> PaginatedList[RenewableRentalCompact]:
        """Get a paginated list of all renewable reservations associated with this account.

        Returns:
            PaginatedList[RenewableRentalCompact]: A paginated list of renewable rental reservations.
        """
        action = _Action(method="GET", href="/api/pub/v2/reservations/rental/renewable")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=RenewableRentalCompact.from_api, api_context=self.client
        )

    def list_nonrenewable(self) -> PaginatedList[NonrenewableRentalCompact]:
        """Get a paginated list of all non-renewable reservations associated with this account.

        Returns:
            PaginatedList[NonrenewableRentalCompact]: A paginated list of non-renewable rental reservations.
        """
        action = _Action(method="GET", href="/api/pub/v2/reservations/rental/nonrenewable")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=NonrenewableRentalCompact.from_api, api_context=self.client
        )

    def renewable_details(
        self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]
    ) -> RenewableRentalExpanded:
        """Get detailed information about a renewable reservation by ID.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded]): The ID or instance of the renewable reservation to retrieve.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            RenewableRentalExpanded: The detailed information about the renewable reservation.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}")
        response = self.client._perform_action(action)

        return RenewableRentalExpanded.from_api(response.data)

    def nonrenewable_details(
        self, reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]
    ) -> NonrenewableRentalExpanded:
        """Get detailed information about a non-renewable reservation by ID.

        Args:
            reservation_id (Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the non-renewable reservation to retrieve.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            NonrenewableRentalExpanded: The detailed information about the non-renewable reservation.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of NonrenewableRentalCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/rental/nonrenewable/{reservation_id}")
        response = self.client._perform_action(action)

        return NonrenewableRentalExpanded.from_api(response.data)

    def check_health(
        self,
        reservation_id: Union[
            str,
            Reservation,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
        ],
    ) -> LineHealth:
        """Check the health status of a reservation.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the reservation to check.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            LineHealth: The health status information for the reservation.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(
                reservation_id,
                (
                    Reservation,
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                ),
            )
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError(
                "reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded or NonrenewableRentalCompact/Expanded."
            )

        action = _Action(method="GET", href=f"/api/pub/v2/reservations/{reservation_id}/health")
        response = self.client._perform_action(action)

        return LineHealth.from_api(response.data)

    def update_renewable(
        self,
        reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded],
        data: RenewableRentalUpdateRequest = None,
        *,
        user_notes: str = None,
        include_for_renewal: bool = None,
        mark_all_sms_read: bool = None,
    ) -> bool:
        """Update properties of a renewable reservation.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded]): The ID or instance of the renewable reservation to update.
            data (RenewableRentalUpdateRequest, optional): Data to update. All kwargs will overwrite values in this object. Defaults to None.
            user_notes (str, optional): Custom notes for the reservation. Defaults to None.
            include_for_renewal (bool, optional): Whether to include this reservation in automatic renewals. Defaults to None.
            mark_all_sms_read (bool, optional): Whether to mark all SMS messages as read. Defaults to None.

        Raises:
            ValueError: If reservation_id is not valid or if no fields are provided to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        update_request = (
            RenewableRentalUpdateRequest(
                user_notes=user_notes or data.user_notes,
                include_for_renewal=(
                    include_for_renewal if include_for_renewal is not None else data.include_for_renewal
                ),
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

    def update_nonrenewable(
        self,
        reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded],
        data: NonrenewableRentalUpdateRequest = None,
        *,
        user_notes: str = None,
        mark_all_sms_read: bool = None,
    ) -> bool:
        """Update properties of a non-renewable reservation.

        Args:
            reservation_id (Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the non-renewable reservation to update.
            data (NonrenewableRentalUpdateRequest, optional): Data to update.  All kwargs will overwrite values in this object. Defaults to None.
            user_notes (str, optional): Custom notes for the reservation. Defaults to None.
            mark_all_sms_read (bool, optional): Whether to mark all SMS messages as read. Defaults to None.

        Raises:
            ValueError: If reservation_id is not valid or if no fields are provided to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
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

    def refund_renewable(self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]) -> bool:
        """Request a refund for a renewable reservation.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded]): The ID or instance of the renewable reservation to refund.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            bool: True if the refund request was successful, False otherwise.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}/refund")
        self.client._perform_action(action)

        return True

    def refund_nonrenewable(
        self, reservation_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]
    ) -> bool:
        """Request a refund for a non-renewable reservation.

        Args:
            reservation_id (Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the non-renewable reservation to refund.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            bool: True if the refund request was successful, False otherwise.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (NonrenewableRentalCompact, NonrenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of NonrenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/nonrenewable/{reservation_id}/refund")
        self.client._perform_action(action)

        return True

    def renew_overdue(self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]) -> bool:
        """Renew an overdue renewable reservation.

        This will cost api balance, so ensure you have sufficient funds before calling this method.

        This method is used to manually renew individual overdue renewable reservations.
        For bulk renewal of active rentals, use the billing cycle renewal method instead.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded]): The ID or instance of the overdue renewable reservation to renew.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            bool: True if the renewal was successful, False otherwise.
        """
        reservation_id = (
            reservation_id.id
            if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded))
            else reservation_id
        )

        if not reservation_id or not isinstance(reservation_id, str):
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/reservations/rental/renewable/{reservation_id}/renew")
        self.client._perform_action(action)

        return True

    def extend_nonrenewable(
        self,
        data: RentalExtensionRequest = None,
        *,
        extension_duration: RentalDuration = None,
        rental_id: Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded] = None,
    ) -> bool:
        """Extend the duration of a non-renewable reservation.

        This will cost api balance, so ensure you have sufficient funds before calling this method.

        Args:
            data (RentalExtensionRequest, optional): The extension details. All kwargs will overwrite values in this object. Defaults to None.
            extension_duration (RentalDuration, optional): The duration to extend the reservation by. Defaults to None.
            rental_id (Union[str, NonrenewableRentalCompact, NonrenewableRentalExpanded], optional): The ID or instance of the non-renewable reservation to extend. Defaults to None.

        Raises:
            ValueError: If both extension_duration and rental_id are not provided.

        Returns:
            bool: True if the extension was successful, False otherwise.
        """
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
