from .action import _ActionPerformer, _Action
from typing import List
from .generated.generated_enums import ReservationSaleCompact, ReservationSaleExpanded
from .paginated_list import PaginatedList

class SalesAPI:
    """API endpoints related to sales."""
    
    def __init__(self, client: _ActionPerformer):
        self.client = client
    
    def get_all_sales(self) -> PaginatedList[ReservationSaleCompact]:
        """Get a list of your reservation sales."""
        action = _Action(method="GET", href="/api/pub/v2/sales")
        response = self.client._perform_action(action)
        
        return PaginatedList(
            request_json=response.data,
            parse_item=ReservationSaleCompact.from_api,
            api_context=self.client
        )

    def get_sale(self, sale_id: str) -> ReservationSaleExpanded:
        """Gets more information about a specific sale."""
        action = _Action(method="GET", href=f"/api/pub/v2/sales/{sale_id}")
        response = self.client._perform_action(action)

        return ReservationSaleExpanded.from_api(response.data)

    # Can we move this to .reservations instead of .sales?