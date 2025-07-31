from .action import _ActionPerformer, _Action
from typing import List, Union
from .data import (
    BillingCycleCompact,
    BillingCycleExpanded,
    BillingCycleUpdateRequest,
    BillingCycleRenewalInvoicePreview,
    BillingCycleRenewalInvoice,
)
from .paginated_list import PaginatedList


class BillingCycleAPI:
    """API endpoints related to billing cycles.
    Renewable rentals are associated with billing cycles and can be manually assigned on rental creation or automatically assigned.
    A single billing cycle can have multiple renewable rentals.
    Billing cycles can be updated, renewed, and queried for invoices."""

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def list(self) -> PaginatedList[BillingCycleCompact]:
        """Fetch all billing cycles associated with this account."""
        action = _Action(method="GET", href="/api/pub/v2/billing-cycles")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=BillingCycleCompact.from_api, api_context=self.client
        )

    def get(self, billing_cycle_id: str) -> BillingCycleExpanded:
        """Get the details of a billing cycle by ID.

        Args:
            billing_cycle_id (str): The ID of the billing cycle to retrieve.

        Returns:
            BillingCycleExpanded: The detailed information about the billing cycle.
        """
        action = _Action(method="GET", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}")
        response = self.client._perform_action(action)

        return BillingCycleExpanded.from_api(response.data)

    def update(
        self,
        billing_cycle: Union[str, BillingCycleCompact, BillingCycleExpanded],
        data: BillingCycleUpdateRequest = None,
        *,
        reminders_enabled: bool = None,
        nickname: str = None,
    ) -> bool:
        """Update a billing cycle.

        Args:
            billing_cycle (Union[str, BillingCycleCompact, BillingCycleExpanded]): The ID or instance of the billing cycle to update.
            data (BillingCycleUpdateRequest, optional): Data to update. Overwritten by kwargs. Defaults to None.
            reminders_enabled (bool, optional): Whether email reminders are enabled. Defaults to None.
            nickname (str, optional): Your custom string to identify the billing cycle. Defaults to None.

        Raises:
            ValueError: If billing_cycle is not a valid ID or instance, or if no fields are provided to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
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

        if not billing_cycle_id or not isinstance(billing_cycle_id, str):
            raise ValueError("billing_cycle must be a valid ID or instance of BillingCycleCompact/Expanded.")

        if not update_request or (not update_request.reminders_enabled and not update_request.nickname):
            raise ValueError("At least one field must be updated: reminders_enabled or nickname.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}")
        response = self.client._perform_action(action, json=update_request.to_api())

        return True

    def invoices(
        self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]
    ) -> PaginatedList[BillingCycleRenewalInvoice]:
        """Get invoices for a specific billing cycle.

        Args:
            billing_cycle_id (Union[str, BillingCycleCompact, BillingCycleExpanded]): The ID or instance of the billing cycle to retrieve invoices for.

        Raises:
            ValueError: If billing_cycle_id is not a valid ID or instance.

        Returns:
            PaginatedList[BillingCycleRenewalInvoice]: A paginated list of billing cycle renewal invoices.
        """

        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id or not isinstance(billing_cycle_id, str):
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="GET", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/invoices")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=BillingCycleRenewalInvoice.from_api, api_context=self.client
        )

    def preview(
        self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]
    ) -> BillingCycleRenewalInvoice:
        """Preview the next billing cycle invoice.

        Args:
            billing_cycle_id (Union[str, BillingCycleCompact, BillingCycleExpanded]): The ID or instance of the billing cycle to preview.

        Raises:
            ValueError: If billing_cycle_id is not a valid ID or instance.

        Returns:
            BillingCycleRenewalInvoice: The preview of the next billing cycle invoice.
        """

        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id or not isinstance(billing_cycle_id, str):
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/next-invoice")
        response = self.client._perform_action(action)
        return BillingCycleRenewalInvoicePreview.from_api(response.data)

    def renew(self, billing_cycle_id: Union[str, BillingCycleCompact, BillingCycleExpanded]) -> bool:
        """Renew the active rentals on your billing cycle.
        Will not renew overdue rentals. To renew overdue rentals, you must explicitly call `textverified.reservations.renew_overdue_renewable_reservation` on each overdue rental.

        Args:
            billing_cycle_id (Union[str, BillingCycleCompact, BillingCycleExpanded]): The ID or instance of the billing cycle to renew.

        Raises:
            ValueError: If billing_cycle_id is not a valid ID or instance.

        Returns:
            bool: True if the billing cycle was renewed successfully, False otherwise.
        """

        billing_cycle_id = (
            billing_cycle_id.id
            if isinstance(billing_cycle_id, (BillingCycleCompact, BillingCycleExpanded))
            else billing_cycle_id
        )

        if not billing_cycle_id or not isinstance(billing_cycle_id, str):
            raise ValueError("billing_cycle_id must be a valid ID or instance of BillingCycleCompact/Expanded.")

        action = _Action(method="POST", href=f"/api/pub/v2/billing-cycles/{billing_cycle_id}/renew")
        self.client._perform_action(action)

        return True
