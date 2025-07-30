from .action import _ActionPerformer, _Action
from typing import List, Union
from .data import ReservationSaleCompact, ReservationSaleExpanded
from .paginated_list import PaginatedList


class SalesAPI:
    """API endpoints related to sales.
    Sales are created when a reservation or verification is sold, and can be queried for details.
    """

    def __init__(self, client: _ActionPerformer):
        self.client = client

    def list(self) -> PaginatedList[ReservationSaleCompact]:
        """Fetch all sales associated with this account.

        Returns:
            PaginatedList[ReservationSaleCompact]: A paginated list of sales.
        """
        action = _Action(method="GET", href="/api/pub/v2/sales")
        response = self.client._perform_action(action)

        return PaginatedList(
            request_json=response.data, parse_item=ReservationSaleCompact.from_api, api_context=self.client
        )

    def get(self, sale_id: Union[str, ReservationSaleCompact, ReservationSaleExpanded]) -> ReservationSaleExpanded:
        """Retrieve details of a specific sale

        Args:
            sale_id (Union[str, ReservationSaleCompact, ReservationSaleExpanded]): The ID or instance of the sale to retrieve.

        Raises:
            ValueError: If sale_id is not a valid ID or instance.

        Returns:
            ReservationSaleExpanded: The details of the requested sale.
        """

        sale_id = sale_id.id if isinstance(sale_id, (ReservationSaleCompact, ReservationSaleExpanded)) else sale_id
        if not isinstance(sale_id, str):
            raise ValueError(
                "sale_id must be a string or an instance of ReservationSaleCompact or ReservationSaleExpanded"
            )

        action = _Action(method="GET", href=f"/api/pub/v2/sales/{sale_id}")
        response = self.client._perform_action(action)

        return ReservationSaleExpanded.from_api(response.data)

    # Can we move this to .reservations instead of .sales?
