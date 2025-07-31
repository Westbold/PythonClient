from .action import _ActionPerformer, _Action
from typing import List, Union
from .data import (
    Reservation,
    RenewableRentalCompact,
    RenewableRentalExpanded,
    NonrenewableRentalCompact,
    NonrenewableRentalExpanded,
    WakeRequest,
    WakeResponse,
    UsageWindowEstimateRequest,
)
import time
import datetime


class WakeAPI:
    """API endpoints related to waking lines."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def create(
        self,
        reservation_id: Union[
            str,
            Reservation,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
        ],
    ) -> WakeResponse:
        """Create a wake request for a rental reservation.

        Wake requests are used to activate rental numbers that are in sleep mode, making them available
        to receive SMS messages and voice calls. The wake process schedules a usage window during which
        the number will be active.

        Args:
            reservation_id (Union[str, Reservation, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the reservation to wake.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            WakeResponse: The wake request details including scheduling information and usage window.
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
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        # Actually takes in a WakeRequest, may need to change this later if API spec changes

        action = _Action(method="POST", href="/api/pub/v2/wake-requests")
        response = self.client._perform_action(action, json=WakeRequest(reservation_id=reservation_id).to_api())

        # Note - response.data is another action to get a WakeResponse

        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return WakeResponse.from_api(response.data)

    def get(self, wake_request_id: Union[str, WakeResponse]) -> WakeResponse:
        """Get detailed information about a wake request by ID.

        Args:
            wake_request_id (Union[str, WakeResponse]): The ID or instance of the wake request to retrieve.

        Raises:
            ValueError: If wake_request_id is not a valid ID or instance.

        Returns:
            WakeResponse: The detailed information about the wake request including status and timing.
        """
        wake_request_id = wake_request_id.id if isinstance(wake_request_id, WakeResponse) else wake_request_id

        if not wake_request_id or not isinstance(wake_request_id, str):
            raise ValueError("wake_request_id must be a valid ID or instance of WakeResponse.")

        action = _Action(method="GET", href=f"/api/pub/v2/wake-requests/{wake_request_id}")
        response = self.client._perform_action(action)

        return WakeResponse.from_api(response.data)

    def estimate_usage_window(
        self,
        reservation_id: Union[
            str,
            Reservation,
            RenewableRentalCompact,
            RenewableRentalExpanded,
            NonrenewableRentalCompact,
            NonrenewableRentalExpanded,
        ],
    ) -> UsageWindowEstimateRequest:
        """Estimate the usage window timing for a reservation wake request.

        This method provides an estimate of when a wake request would be scheduled without actually
        creating the wake request. Useful for planning when to wake a number for time-sensitive operations.

        Args:
            reservation_id (Union[str, Reservation, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the reservation to estimate wake timing for.

        Raises:
            ValueError: If reservation_id is not a valid ID or instance.

        Returns:
            UsageWindowEstimateRequest: The estimated usage window timing information.
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
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href="/api/pub/v2/wake-requests/estimate")
        response = self.client._perform_action(action, json=WakeRequest(reservation_id=reservation_id).to_api())

        return UsageWindowEstimateRequest.from_api(response.data)

    def wait_for_number_wake(
        self,
        reservation_id: Union[
            str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded
        ],
        poll_frequency: float = 5.0,
    ) -> WakeResponse:
        """Create a wake request and wait for the number to become active.

        This is a convenience method that combines creating a wake request and waiting for it to complete.
        The method will block until the usage window begins and the number is ready to receive SMS/calls.

        Args:
            reservation_id (Union[str, RenewableRentalCompact, RenewableRentalExpanded, NonrenewableRentalCompact, NonrenewableRentalExpanded]): The ID or instance of the reservation to wake and wait for.
            poll_frequency (float): The frequency (in seconds) to poll for the wake request status. Estimated usage window may change after wake request creation. Default is 5 seconds.

        Raises:
            ValueError: If reservation_id is not valid or if the wake request creation fails.

        Returns:
            WakeResponse: The wake response containing the usage window start time, end time, and other details.
        """
        wake_response = self.create(reservation_id)
        if not wake_response:
            raise ValueError("Failed to create wake request.")

        return self.wait_for_wake_request(wake_response, poll_frequency=poll_frequency)

    def wait_for_wake_request(
        self, wake_request_id: Union[str, WakeResponse], poll_frequency: float = 5.0
    ) -> WakeResponse:
        """Wait for an existing wake request to complete and become active.

        This method blocks execution until the wake request's usage window starts, meaning the number
        is ready to receive SMS messages and voice calls. Use this when you have an existing wake request
        and need to wait for it to become active.

        Args:
            wake_request_id (Union[str, WakeResponse]): The ID or instance of the wake request to wait for.
            poll_frequency (float): The frequency (in seconds) to poll for the wake request status. Estimated usage window may change after wake request creation.

        Raises:
            ValueError: If wake_request_id is not valid or if the wake request is not properly scheduled.

        Returns:
            WakeResponse: The wake response containing the usage window start time, end time, and other details.
        """
        # Get full object if given an ID
        if isinstance(wake_request_id, str):
            wake_request_id = self.get(wake_request_id)

        if not isinstance(wake_request_id, WakeResponse):
            raise ValueError("wake_request_id must be a valid ID or instance of WakeResponse.")

        if (
            not wake_request_id.is_scheduled
            or not wake_request_id.usage_window_start
            or not wake_request_id.usage_window_end
        ):
            raise ValueError("Wake request must be scheduled with a valid usage window.")

        # Wait until the usage window starts
        while datetime.datetime.now(datetime.timezone.utc) < wake_request_id.usage_window_start:
            seconds_till_start = (
                wake_request_id.usage_window_start - datetime.datetime.now(datetime.timezone.utc)
            ).total_seconds()
            time.sleep(min(seconds_till_start, poll_frequency))
            wake_request_id = self.get(wake_request_id)

        return wake_request_id
