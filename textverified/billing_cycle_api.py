from .action import _ActionPerformer, _Action
from typing import List, Union
from .generated.generated_enums import (
    BillingCycleCompact,
    BillingCycleExpanded,
    BillingCycleUpdateRequest,
    BillingCycleRenewalInvoicePreview,
    BillingCycleRenewalInvoice,
)
from .paginated_list import PaginatedList


class BillingCycleAPI:
    """API endpoints related to billing cycles."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def get_billing_cycles(self) -> PaginatedList[BillingCycleCompact]:
        """Get a list of your billing cycles."""
        action = _Action(method="GET", href="/api/pub/v2/billing-cycles")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=BillingCycleCompact.from_api, api_context=self.client
        )

    def get_billing_cycle(self, billing_cycle_id: str) -> BillingCycleExpanded:
        """Gets more information about a specific billing cycle."""
        action = _Action(method="GET", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}")
        response = self.client._perform_action(action)

        return BillingCycleExpanded.from_api(response.data)

    def update_billing_cycle(
        self,
        billing_cycle: Union[str, BillingCycleCompact, BillingCycleExpanded],
        data: BillingCycleUpdateRequest = None,
        *,
        reminders_enabled: bool = None,
        nickname: str = None,
    ) -> bool:
        """Updates a specific billing cycle."""
        billing_cycle_id = (
            billing_cycle.id
            if isinstance(billing_cycle, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle
        )

        update_request = (
            BillingCycleUpdateRequest(
                reminders_enabled=reminders_enabled if reminders_enabled is not None else data.reminders_enabled,
                nickname=nickname or data.nickname,
            )
            if data
            else BillingCycleUpdateRequest(reminders_enabled=reminders_enabled, nickname=nickname)
        )

        if not billing_cycle_id:
            raise ValueError("billing_cycle must be a valid ID or instance of BillingCycleCompact/Expanded.")

        if not update_request or (not update_request.reminders_enabled and not update_request.nickname):
            raise ValueError("At least one field must be updated: reminders_enabled or nickname.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}")
        response = self.client._perform_action(action, json=update_request.to_api())

        return True

    def get_billing_invoices(
        self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]
    ) -> PaginatedList[BillingCycleRenewalInvoice]:
        """Get invoices for a specific billing cycle."""
        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id:
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/invoices")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=BillingCycleRenewalInvoice.from_api, api_context=self.client
        )

    def preview_next_billing_cycle(
        self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]
    ) -> BillingCycleRenewalInvoice:
        """Preview the next billing cycle invoice."""
        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id:
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/next-invoice")
        response = self.client._perform_action(action)
        return BillingCycleRenewalInvoicePreview.from_api(response.data)

    def renew_billing_cycle(self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]) -> bool:
        """Renew a specific billing cycle."""
        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id:
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/renew")
        self.client._perform_action(action)

        return True
