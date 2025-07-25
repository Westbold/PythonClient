from .action import _ActionPerformer, _Action
from typing import List
from .generated.generated_enums import (
    RenewableRentalCompact, RenewableRentalExpanded,
    WakeRequest, WakeResponse, UsageWindowEstimateRequest
)

class WakeAPI:
    """API endpoints related to waking lines."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def create_wake_request(self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]) -> WakeResponse:
        """Create a wake request for a specific reservation."""
        reservation_id = reservation_id.id if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded)) else reservation_id

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        # Actually takes in a WakeRequest, may need to change this later if API spec changes

        action = _Action(method="POST", href="/api/pub/v2/wake-requests")
        response = self.client._perform_action(action, json=WakeRequest(reservation_id=reservation_id))

        # Note - response.data is another action to get a WakeResponse

        action = _Action.from_api(response.data)
        response = self.client._perform_action(action)

        return WakeResponse.from_api(response.data)

    def get_wake_request(self, wake_request_id: Union[str, WakeResponse]) -> WakeResponse:
        """Get details of a specific wake request."""
        wake_request_id = wake_request_id.id if isinstance(wake_request_id, WakeResponse) else wake_request_id

        if not wake_request_id:
            raise ValueError("wake_request_id must be a valid ID or instance of WakeResponse.")

        action = _Action(method="GET", href=f"/api/pub/v2/wake-requests/{wake_request_id}")
        response = self.client._perform_action(action)

        return WakeResponse.from_api(response.data)

    def estimate_usage_window(self, reservation_id: Union[str, RenewableRentalCompact, RenewableRentalExpanded]) -> UsageWindowEstimateRequest:
        """Estimate the usage window for a specific reservation."""
        reservation_id = reservation_id.id if isinstance(reservation_id, (RenewableRentalCompact, RenewableRentalExpanded)) else reservation_id

        if not reservation_id:
            raise ValueError("reservation_id must be a valid ID or instance of RenewableRentalCompact/Expanded.")

        action = _Action(method="POST", href="/api/pub/v2/wake-requests/estimate")
        response = self.client._perform_action(action, json=WakeRequest(reservation_id=reservation_id))

        return UsageWindowEstimateRequest.from_api(response.data)

