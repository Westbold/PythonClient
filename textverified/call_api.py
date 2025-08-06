from .action import _ActionPerformer, _Action
from typing import List, Union
from .paginated_list import PaginatedList
from .data import (
    Call,
    Reservation,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    RenewableRentalCompact,
    RenewableRentalExpanded,
    VerificationCompact,
    VerificationExpanded,
    ReservationType,
    TwilioCallingContextDto,
)


class CallAPI:
    """API endpoints related to calls."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def list(
        self,
        data: Union[
            Reservation,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            VerificationCompact,
            VerificationExpanded,
        ] = None,
        *,
        to_number: str = None,
        reservation_type: ReservationType = None,
    ) -> PaginatedList[Call]:
        """List calls to rentals and verifications associated with this account.

        You can retrieve all calls across all your rentals and verifications, or filter by specific criteria.
        When providing a rental or verification object, calls for that specific number will be returned.

        Args:
            data (Union[Reservation, NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded], optional): A rental or verification object to get calls for. The phone number will be extracted from this object. Defaults to None.
            to_number (str, optional): Filter calls by the destination phone number. Cannot be used together with data parameter. Defaults to None.
            reservation_type (ReservationType, optional): Filter calls by reservation type (renewable, non-renewable, verification). Cannot be used when providing a data object. Defaults to None.

        Raises:
            ValueError: If both data and to_number are provided, or if reservation_type is specified when using a rental/verification object.

        Returns:
            PaginatedList[Call]: A paginated list of calls matching the specified criteria.
        """

        # Extract needed data from provided objects
        reservation_id = None
        if data and isinstance(
            data,
            (
                NonrenewableRentalCompact,
                NonrenewableRentalExpanded,
                RenewableRentalCompact,
                RenewableRentalExpanded,
                VerificationCompact,
                VerificationExpanded,
            ),
        ):
            if to_number:
                raise ValueError("Cannot specify both rental/verification data and to_number.")
            to_number = data.number

            if reservation_type is not None:
                raise ValueError("Cannot specify reservation_type when using a rental or verification object.")

        if isinstance(
            data,
            (
                Reservation,
                NonrenewableRentalCompact,
                NonrenewableRentalExpanded,
                RenewableRentalCompact,
                RenewableRentalExpanded,
            ),
        ):
            reservation_id = data.id

        # Construct url params
        params = dict()
        if to_number:
            params["to"] = to_number

        if reservation_id:
            params["reservationId"] = reservation_id

        if isinstance(reservation_type, ReservationType):
            params["reservationType"] = reservation_type.to_api()

        # Construct and perform the action
        action = _Action(method="GET", href="/api/pub/v2/calls")
        response = self.client._perform_action(action, params=params)

        return PaginatedList(request_json=response.data, parse_item=Call.from_api, api_context=self.client)

    def open_call_session(
        self,
        reservation: Union[
            str,
            Reservation,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            VerificationCompact,
            VerificationExpanded,
        ],
    ) -> TwilioCallingContextDto:
        """Create a call access token for incoming calls.

        This endpoint generates a short-lived Twilio access token.
        The token is associated with a reservation ID, which is obtained from a voice verification.
        This token is then used with Twilio's SDKs to handle an incoming call.

        **Warning:**
        This is an advanced integration. No support will be provided for implementation or debugging.
        You are responsible for implementing the provider's integration to handle incoming calls successfully.

        Workflow:
        1. Creating a voice verification and getting the corresponding `reservation id`.
            See: `Creating a voice verification <docs/api/v2#post-/api/pub/v2/verifications>`_
        2. Posting to this endpoint to obtain a short-lived Twilio access token associated with the `reservation id`.
        3. Using the access token with Twilio's integration to handle an incoming call.
            See: `Twilio's integration <https://www.twilio.com/docs/voice/sdks/javascript>`_

        Args:
            reservation (Union[str, Reservation, NonrenewableRentalCompact, NonrenewableRentalExpanded, RenewableRentalCompact, RenewableRentalExpanded, VerificationCompact, VerificationExpanded]): The reservation ID or object to create a call session for.

        Returns:
            TwilioCallingContextDto: The Twilio calling context containing the access token and other details.
        """

        reservation_id = (
            reservation.id
            if isinstance(
                reservation,
                (
                    Reservation,
                    NonrenewableRentalCompact,
                    NonrenewableRentalExpanded,
                    RenewableRentalCompact,
                    RenewableRentalExpanded,
                    VerificationCompact,
                    VerificationExpanded,
                ),
            )
            else reservation
        )

        if not isinstance(reservation_id, str) or not reservation_id.strip():
            raise ValueError("reservation_id must be a valid ID or instance of Reservation/Verification.")

        action = _Action(method="POST", href="/api/pub/v2/calls/access-token")
        response = self.client._perform_action(action, json={"reservationId": reservation_id})

        return TwilioCallingContextDto.from_api(response.data)
