from .action import _ActionPerformer, _Action
from typing import List, Union, Generic, TypeVar, Callable
from enum import Enum
from .paginated_list import PaginatedList
from dataclasses import dataclass
from .data import (
    LineReservationType,
    ReservationType,
    Reservation,
    NonrenewableRentalExpanded,
    RenewableRentalExpanded,
    VerificationExpanded,
    ReservationSaleExpanded,
    BillingCycleExpanded,
    WakeResponse,
    BackOrderReservationExpanded,
    RentalExtensionRequest,
    RentalDuration
)
from .verifications_api import VerificationsAPI
from .reservations_api import ReservationsAPI
from .billing_cycle_api import BillingCycleAPI
from .sales_api import SalesAPI
from .wake_api import WakeAPI

class MockIdentifierType(Enum):
    """Mock identifier types"""
    MockWakeRequest = 1,
    MockSale = 2,
    MockBackorderReservation = 3,
    # MockReservationRequest = 4, -- not needed for api calls
    MockBillingCycle = 5,
    MockReservation = 6,
    MockVerification = 7,
    MockRental = 8,
    MockTarget = 9,
    MockExtension = 10

class MockReceivePolicy(Enum):
    """MockReceivePolicy: determines what should be returned when polling for messages or calls"""
    NoIncoming = 0
    IncomingText = 1
    IncomingCall = 2
    IncomingTextAndCall = 3 
    
class MockBehavior(Enum):
    """MockBehavior: determines how the mock should behave. If set to FailRandomly, will fail 1/3 of the time."""
    Succeeds = 0
    AlwaysFails = 1
    FailsRandomly = 2

def _construct_mock(*args):
    assert len(args) > 0
    return "_$_".join(str(arg) for arg in args)

T = TypeVar('T')

@dataclass(frozen=True)
class MockObject(Generic[T]):
    """Base class for mock objects."""
    id: str
    _get_function: Callable[[], T]
    
    @property
    def name(self) -> str:
        return self.id

    def get(self) -> T:
        return self._get_function()
    
    def __eq__(self, value):
        if not isinstance(value, MockObject):
            return NotImplemented
        return self.id == value.id
    
    def __hash__(self):
        return hash(self.id)


class Mocking:
    """Constructs mock identifiers for use with the TextVerified API."""

    def __init__(self, verifications_api: VerificationsAPI, reservations_api: ReservationsAPI, billing_cycle_api: BillingCycleAPI, sales_api: SalesAPI, wake_api: WakeAPI):
        self.verifications_api = verifications_api
        self.reservations_api = reservations_api
        self.billing_cycle_api = billing_cycle_api
        self.sales_api = sales_api
        self.wake_api = wake_api

    def target(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall) -> str:
        """Constructs a mock target identifier.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.

        Returns:
            str: The constructed mock target identifier.
        """
        return _construct_mock(MockIdentifierType.MockTarget.name, behavior.name, receive_policy.name)
    
    def service(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall) -> str:
        """Constructs a mock service name identifier. Identical to Mocking.target.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.

        Returns:
            str: The constructed mock service name identifier.
        """
        return self.target(behavior, receive_policy)

    def reservation(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall, reservation_type: ReservationType = ReservationType.NONRENEWABLE, ) -> MockObject[Union[RenewableRentalExpanded, NonrenewableRentalExpanded]]:
        line_type = LineReservationType.VERIFICATION if reservation_type == ReservationType.VERIFICATION else LineReservationType.RENTAL
        mock_id = _construct_mock(MockIdentifierType.MockReservation.name, behavior.name, line_type.name, reservation_type.name, receive_policy.name)
        return MockObject[Union[RenewableRentalExpanded, NonrenewableRentalExpanded]](id=mock_id, _get_function=lambda: self.reservations_api.details(mock_id))
    
    def rental(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall, reservation_type: ReservationType = ReservationType.NONRENEWABLE,) -> MockObject[Union[RenewableRentalExpanded, NonrenewableRentalExpanded]]:
        """Constructs a mock rental identifier that returns rental details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.
            reservation_type (ReservationType, optional): The type of rental. Defaults to ReservationType.NONRENEWABLE.

        Returns:
            MockObject[Union[RenewableRentalExpanded, NonrenewableRentalExpanded]]: A mock object that can retrieve rental details.
        """
        line_type = LineReservationType.VERIFICATION if reservation_type == ReservationType.VERIFICATION else LineReservationType.RENTAL
        mock_id = _construct_mock(MockIdentifierType.MockRental.name, behavior.name, line_type.name, reservation_type.name, receive_policy.name)
        return MockObject[Union[RenewableRentalExpanded, NonrenewableRentalExpanded]](id=mock_id, _get_function=lambda: self.reservations_api.details(mock_id))
    
    def verification(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall) -> MockObject[VerificationExpanded]:
        """Constructs a mock verification identifier that returns verification details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.

        Returns:
            MockObject[VerificationExpanded]: A mock object that can retrieve verification details.
        """
        mock_id = _construct_mock(MockIdentifierType.MockVerification.name, behavior.name, LineReservationType.VERIFICATION.name, ReservationType.VERIFICATION.name, receive_policy.name)
        return MockObject[VerificationExpanded](id=mock_id, _get_function=lambda: self.verifications_api.details(mock_id))
    
    def sale(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall, reservation_type: ReservationType = ReservationType.NONRENEWABLE,) -> MockObject[ReservationSaleExpanded]:
        """Constructs a mock sale identifier that returns sale details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.
            reservation_type (ReservationType, optional): The type of reservation for the sale. Defaults to ReservationType.NONRENEWABLE.

        Returns:
            MockObject[ReservationSaleExpanded]: A mock object that can retrieve sale details.
        """
        line_type = LineReservationType.VERIFICATION if reservation_type == ReservationType.VERIFICATION else LineReservationType.RENTAL
        mock_id = _construct_mock(MockIdentifierType.MockSale.name, behavior.name, line_type.name, reservation_type.name, receive_policy.name)
        return MockObject[ReservationSaleExpanded](id=mock_id, _get_function=lambda: self.sales_api.get(mock_id))
    
    def backorder_sale(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall, reservation_type: ReservationType = ReservationType.NONRENEWABLE,) -> MockObject[BackOrderReservationExpanded]:
        """Constructs a mock backorder sale identifier that returns backorder details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.
            reservation_type (ReservationType, optional): The type of reservation for the backorder. Defaults to ReservationType.NONRENEWABLE.

        Returns:
            MockObject[BackOrderReservationExpanded]: A mock object that can retrieve backorder details.
        """
        line_type = LineReservationType.VERIFICATION if reservation_type == ReservationType.VERIFICATION else LineReservationType.RENTAL
        mock_id = _construct_mock(MockIdentifierType.MockBackorderReservation.name, behavior.name, line_type.name, reservation_type.name, receive_policy.name)
        return MockObject[BackOrderReservationExpanded](id=mock_id, _get_function=lambda: self.reservations_api.backorder(mock_id))
    
    def billing_cycle(self, behavior: MockBehavior = MockBehavior.Succeeds) -> MockObject[BillingCycleExpanded]:
        """Constructs a mock billing cycle identifier that returns billing cycle details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.

        Returns:
            MockObject[BillingCycleExpanded]: A mock object that can retrieve billing cycle details.
        """
        mock_id = _construct_mock(MockIdentifierType.MockBillingCycle.name, behavior.name)
        return MockObject[BillingCycleExpanded](id=mock_id, _get_function=lambda: self.billing_cycle_api.get(mock_id))
    
    def extension(self, behavior: MockBehavior = MockBehavior.Succeeds) -> MockObject[RentalExtensionRequest]:
        """Constructs a mock extension identifier.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.

        Returns:
            MockObject[RentalExtensionRequest]: A mock object that can retrieve a rental extension request.
        """
        mock_id = _construct_mock(MockIdentifierType.MockExtension.name, behavior.name)
        return MockObject[RentalExtensionRequest](id=mock_id, _get_function=lambda: RentalExtensionRequest(
            mock_id,
            extension_duration=RentalDuration.THIRTY_DAY
        ))

    def wake_request(self, behavior: MockBehavior = MockBehavior.Succeeds, receive_policy: MockReceivePolicy = MockReceivePolicy.IncomingTextAndCall, reservation_type: ReservationType = ReservationType.NONRENEWABLE,) -> MockObject[WakeResponse]:
        """Constructs a mock wake request identifier that returns wake request details when get() is called.

        Args:
            behavior (MockBehavior, optional): Determines how the mock should behave. Defaults to MockBehavior.Succeeds.
            receive_policy (MockReceivePolicy, optional): Determines what should be returned when polling for messages or calls. Defaults to MockReceivePolicy.IncomingTextAndCall.
            reservation_type (ReservationType, optional): The type of reservation for the wake request. Defaults to ReservationType.NONRENEWABLE.

        Returns:
            MockObject[WakeResponse]: A mock object that can retrieve wake request details.
        """
        line_type = LineReservationType.VERIFICATION if reservation_type == ReservationType.VERIFICATION else LineReservationType.RENTAL
        mock_id = _construct_mock(MockIdentifierType.MockWakeRequest.name, behavior.name, line_type.name, reservation_type.name, receive_policy.name)
        return MockObject[WakeResponse](id=mock_id, _get_function=lambda: self.wake_api.get(mock_id))

