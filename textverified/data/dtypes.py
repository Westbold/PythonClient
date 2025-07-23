"""
Generated enums and dataclasses from Swagger schema
This file is auto-generated. Do not edit manually.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Any
import datetime
import dateutil.parser

class BackOrderState(Enum):
    CREATED = 'created'
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'BackOrderState':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown BackOrderState value: canceled')


class KeysetPaginationDirectionality(Enum):
    FORWARD = 'forward'
    REVERSE = 'reverse'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'KeysetPaginationDirectionality':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown KeysetPaginationDirectionality value: reverse')


class LineReservationType(Enum):
    VERIFICATION = 'verification'
    RENTAL = 'rental'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'LineReservationType':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown LineReservationType value: rental')


class RentalDuration(Enum):
    ONE_DAY = 'oneDay'
    THREE_DAY = 'threeDay'
    SEVEN_DAY = 'sevenDay'
    FOURTEEN_DAY = 'fourteenDay'
    THIRTY_DAY = 'thirtyDay'
    NINETY_DAY = 'ninetyDay'
    ONE_YEAR = 'oneYear'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'RentalDuration':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown RentalDuration value: oneYear')


class NumberType(Enum):
    MOBILE = 'mobile'
    VOIP = 'voip'
    LANDLINE = 'landline'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'NumberType':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown NumberType value: landline')


class ReservationCapability(Enum):
    SMS = 'sms'
    VOICE = 'voice'
    SMS_AND_VOICE_COMBO = 'smsAndVoiceCombo'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'ReservationCapability':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown ReservationCapability value: smsAndVoiceCombo')


class ReservationState(Enum):
    VERIFICATION_PENDING = 'verificationPending'
    VERIFICATION_COMPLETED = 'verificationCompleted'
    VERIFICATION_CANCELED = 'verificationCanceled'
    VERIFICATION_TIMED_OUT = 'verificationTimedOut'
    VERIFICATION_REPORTED = 'verificationReported'
    VERIFICATION_REFUNDED = 'verificationRefunded'
    VERIFICATION_REUSED = 'verificationReused'
    VERIFICATION_REACTIVATED = 'verificationReactivated'
    RENEWABLE_ACTIVE = 'renewableActive'
    RENEWABLE_OVERDUE = 'renewableOverdue'
    RENEWABLE_EXPIRED = 'renewableExpired'
    RENEWABLE_REFUNDED = 'renewableRefunded'
    NONRENEWABLE_ACTIVE = 'nonrenewableActive'
    NONRENEWABLE_EXPIRED = 'nonrenewableExpired'
    NONRENEWABLE_REFUNDED = 'nonrenewableRefunded'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'ReservationState':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown ReservationState value: nonrenewableRefunded')


class ReservationType(Enum):
    RENEWABLE = 'renewable'
    NONRENEWABLE = 'nonrenewable'
    VERIFICATION = 'verification'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'ReservationType':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown ReservationType value: verification')


class ReservationSaleState(Enum):
    CREATED = 'created'
    PROCESSING = 'processing'
    FAILED = 'failed'
    SUCCEEDED = 'succeeded'

    def to_api(self) -> str:
        return self.value

    @classmethod
    def from_api(cls, value: str) -> 'ReservationSaleState':
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f'Unknown ReservationSaleState value: succeeded')


@dataclass(frozen=True)
class Account:
    username: str
    current_balance: float

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['username'] = self.username
        api_dict['currentBalance'] = self.current_balance
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Account':
        return cls(
            username=str(data.get("username", None)),
            current_balance=float(data.get("currentBalance", None)),
        )


@dataclass(frozen=True)
class AddOnSnapshot:
    add_on_id: str
    description: str
    renewal_cost: float
    already_renewed: bool

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['addOnId'] = self.add_on_id
        api_dict['description'] = self.description
        api_dict['renewalCost'] = self.renewal_cost
        api_dict['alreadyRenewed'] = self.already_renewed
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'AddOnSnapshot':
        return cls(
            add_on_id=str(data.get("addOnId", None)),
            description=str(data.get("description", None)),
            renewal_cost=float(data.get("renewalCost", None)),
            already_renewed=bool(data.get("alreadyRenewed", None)),
        )


@dataclass(frozen=True)
class AreaCode:
    area_code: str
    """Area code. Optionally supply this value when an ```areaCodeSelectOption``` is in the request body or parameter."""

    state: str
    """The US state associated with the area code."""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['areaCode'] = self.area_code
        api_dict['state'] = self.state
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'AreaCode':
        return cls(
            area_code=str(data.get("areaCode", None)),
            state=str(data.get("state", None)),
        )


@dataclass(frozen=True)
class BackOrderReservationCompact:
    id: str
    service_name: str
    status: BackOrderState

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['serviceName'] = self.service_name
        api_dict['status'] = self.status.to_api()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BackOrderReservationCompact':
        return cls(
            id=str(data.get("id", None)),
            service_name=str(data.get("serviceName", None)),
            status=BackOrderState.from_api(data.get("status", None)),
        )


@dataclass(frozen=True)
class BackOrderReservationWebhookEvent:
    back_order_id: str
    """Id of the back order reservation."""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['backOrderId'] = self.back_order_id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BackOrderReservationWebhookEvent':
        return cls(
            back_order_id=str(data.get("backOrderId", None)),
        )


@dataclass(frozen=True)
class BearerToken:
    token: str
    """Bearer token"""

    expires_in: float
    """Seconds remaining until bearer token expires"""

    expires_at: datetime.datetime
    """Timestamp of when the token will expire"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['token'] = self.token
        api_dict['expiresIn'] = self.expires_in
        api_dict['expiresAt'] = self.expires_at.isoformat()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BearerToken':
        return cls(
            token=str(data.get("token", None)),
            expires_in=float(data.get("expiresIn", None)),
            expires_at=dateutil.parser.parse(data.get("expiresAt", None)),
        )


@dataclass(frozen=True)
class BillingCycleCompact:
    id: str
    """Id of the billing cycle"""

    billing_cycle_ends_at: datetime.datetime
    email_notifications_enabled: bool
    state: str

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['billingCycleEndsAt'] = self.billing_cycle_ends_at.isoformat()
        api_dict['emailNotificationsEnabled'] = self.email_notifications_enabled
        api_dict['state'] = self.state
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleCompact':
        return cls(
            id=str(data.get("id", None)),
            billing_cycle_ends_at=dateutil.parser.parse(data.get("billingCycleEndsAt", None)),
            email_notifications_enabled=bool(data.get("emailNotificationsEnabled", None)),
            state=str(data.get("state", None)),
        )


@dataclass(frozen=True)
class CancelAction:
    can_cancel: bool

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['canCancel'] = self.can_cancel
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'CancelAction':
        return cls(
            can_cancel=bool(data.get("canCancel", None)),
        )


@dataclass(frozen=True)
class PricingSnapshot:
    service_name: str
    """Name of the service."""

    price: float
    """Total cost."""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['serviceName'] = self.service_name
        api_dict['price'] = self.price
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'PricingSnapshot':
        return cls(
            service_name=str(data.get("serviceName", None)),
            price=float(data.get("price", None)),
        )


@dataclass(frozen=True)
class ReactivationAction:
    can_reactivate: bool

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['canReactivate'] = self.can_reactivate
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReactivationAction':
        return cls(
            can_reactivate=bool(data.get("canReactivate", None)),
        )


@dataclass(frozen=True)
class RentalExtensionRequest:
    extension_duration: RentalDuration
    rental_id: str

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['extensionDuration'] = self.extension_duration.to_api()
        api_dict['rentalId'] = self.rental_id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RentalExtensionRequest':
        return cls(
            extension_duration=RentalDuration.from_api(data.get("extensionDuration", None)),
            rental_id=str(data.get("rentalId", None)),
        )


@dataclass(frozen=True)
class ReportAction:
    can_report: bool

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['canReport'] = self.can_report
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReportAction':
        return cls(
            can_report=bool(data.get("canReport", None)),
        )


@dataclass(frozen=True)
class Reservation:
    id: str
    """Id of the reservation"""

    reservation_type: ReservationType
    service_name: str
    """Name of service"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['reservationType'] = self.reservation_type.to_api()
        api_dict['serviceName'] = self.service_name
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Reservation':
        return cls(
            id=str(data.get("id", None)),
            reservation_type=ReservationType.from_api(data.get("reservationType", None)),
            service_name=str(data.get("serviceName", None)),
        )


@dataclass(frozen=True)
class ReservationCreatedWebhookEvent:
    id: str
    """Id of the created reservation."""

    type: LineReservationType

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['type'] = self.type.to_api()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReservationCreatedWebhookEvent':
        return cls(
            id=str(data.get("id", None)),
            type=LineReservationType.from_api(data.get("type", None)),
        )


@dataclass(frozen=True)
class ReservationSaleCompact:
    created_at: datetime.datetime
    id: str
    state: ReservationSaleState
    total_cost: float
    updated_at: datetime.datetime

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['state'] = self.state.to_api()
        api_dict['totalCost'] = self.total_cost
        api_dict['updatedAt'] = self.updated_at.isoformat()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReservationSaleCompact':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            state=ReservationSaleState.from_api(data.get("state", None)),
            total_cost=float(data.get("totalCost", None)),
            updated_at=dateutil.parser.parse(data.get("updatedAt", None)),
        )


@dataclass(frozen=True)
class Service:
    service_name: str
    """Name of the service. Supply this value when a ```ServiceName``` is required."""

    capability: ReservationCapability

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['serviceName'] = self.service_name
        api_dict['capability'] = self.capability.to_api()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Service':
        return cls(
            service_name=str(data.get("serviceName", None)),
            capability=ReservationCapability.from_api(data.get("capability", None)),
        )


@dataclass(frozen=True)
class UsageWindowEstimateRequest:
    reservation_id: str
    """The reservation Id to get the estimated usage window for. If a valid reservation does not exist, a 400 response will be returned."""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['reservationId'] = self.reservation_id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'UsageWindowEstimateRequest':
        return cls(
            reservation_id=str(data.get("reservationId", None)),
        )


@dataclass(frozen=True)
class VerificationCompact:
    created_at: datetime.datetime
    id: str
    service_name: str
    state: ReservationState
    total_cost: float
    number: str

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['totalCost'] = self.total_cost
        api_dict['number'] = self.number
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'VerificationCompact':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            total_cost=float(data.get("totalCost", None)),
            number=str(data.get("number", None)),
        )


@dataclass(frozen=True)
class VerificationPriceCheckRequest:
    service_name: str
    """Example: yahoo"""

    area_code: bool
    """Example: True"""

    carrier: bool
    """Example: True"""

    number_type: NumberType
    capability: ReservationCapability

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['serviceName'] = self.service_name
        api_dict['areaCode'] = self.area_code
        api_dict['carrier'] = self.carrier
        api_dict['numberType'] = self.number_type.to_api()
        api_dict['capability'] = self.capability.to_api()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'VerificationPriceCheckRequest':
        return cls(
            service_name=str(data.get("serviceName", None)),
            area_code=bool(data.get("areaCode", None)),
            carrier=bool(data.get("carrier", None)),
            number_type=NumberType.from_api(data.get("numberType", None)),
            capability=ReservationCapability.from_api(data.get("capability", None)),
        )


@dataclass(frozen=True)
class WakeRequest:
    reservation_id: str
    """The reservation Id to create a wake request for. If a valid reservation does not exist, a 400 response will be returned."""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['reservationId'] = self.reservation_id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WakeRequest':
        return cls(
            reservation_id=str(data.get("reservationId", None)),
        )


@dataclass(frozen=True)
class BackOrderReservationExpanded:
    id: str
    service_name: str
    sale_id: str
    status: BackOrderState
    reservation_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['serviceName'] = self.service_name
        api_dict['saleId'] = self.sale_id
        api_dict['status'] = self.status.to_api()
        api_dict['reservationId'] = (self.reservation_id if self.reservation_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BackOrderReservationExpanded':
        return cls(
            id=str(data.get("id", None)),
            service_name=str(data.get("serviceName", None)),
            sale_id=str(data.get("saleId", None)),
            status=BackOrderState.from_api(data.get("status", None)),
            reservation_id=(str(data.get("reservationId", None)) if data.get("reservationId", None) is not None else None),
        )


@dataclass(frozen=True)
class WebhookEventBackOrderReservationWebhookEvent:
    attempt: int
    """Send attempt count"""

    occurred_at: datetime.datetime
    """When the event occurred"""

    data: BackOrderReservationWebhookEvent
    event: str
    """Name of the event"""

    id: str
    """Id of event"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['attempt'] = self.attempt
        api_dict['occurredAt'] = self.occurred_at.isoformat()
        api_dict['data'] = self.data.to_api()
        api_dict['event'] = self.event
        api_dict['id'] = self.id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WebhookEventBackOrderReservationWebhookEvent':
        return cls(
            attempt=int(data.get("attempt", None)),
            occurred_at=dateutil.parser.parse(data.get("occurredAt", None)),
            data=BackOrderReservationWebhookEvent.from_api(data.get("data", None)),
            event=str(data.get("event", None)),
            id=str(data.get("id", None)),
        )


@dataclass(frozen=True)
class BillingCycleExpanded:
    id: str
    """Id of the billing cycle"""

    renewed_through: datetime.datetime
    billing_cycle_ends_at: datetime.datetime
    email_notifications_enabled: bool
    state: str
    next_auto_renew_attempt: Optional[datetime.datetime] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['renewedThrough'] = self.renewed_through.isoformat()
        api_dict['billingCycleEndsAt'] = self.billing_cycle_ends_at.isoformat()
        api_dict['emailNotificationsEnabled'] = self.email_notifications_enabled
        api_dict['state'] = self.state
        api_dict['nextAutoRenewAttempt'] = (self.next_auto_renew_attempt.isoformat() if self.next_auto_renew_attempt is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleExpanded':
        return cls(
            id=str(data.get("id", None)),
            renewed_through=dateutil.parser.parse(data.get("renewedThrough", None)),
            billing_cycle_ends_at=dateutil.parser.parse(data.get("billingCycleEndsAt", None)),
            email_notifications_enabled=bool(data.get("emailNotificationsEnabled", None)),
            state=str(data.get("state", None)),
            next_auto_renew_attempt=(dateutil.parser.parse(data.get("nextAutoRenewAttempt", None)) if data.get("nextAutoRenewAttempt", None) is not None else None),
        )


@dataclass(frozen=True)
class BillingCycleUpdateRequest:
    """Supplying a value of 'null' or not supplying a value for any nullable properties will cause the property to be ignored.

    """

    reminders_enabled: Optional[bool] = None
    nickname: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['remindersEnabled'] = (self.reminders_enabled if self.reminders_enabled is not None else None)
        api_dict['nickname'] = (self.nickname if self.nickname is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleUpdateRequest':
        return cls(
            reminders_enabled=(bool(data.get("remindersEnabled", None)) if data.get("remindersEnabled", None) is not None else None),
            nickname=(str(data.get("nickname", None)) if data.get("nickname", None) is not None else None),
        )


@dataclass(frozen=True)
class BillingCycleWebhookEvent:
    billing_cycle_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['billingCycleId'] = (self.billing_cycle_id if self.billing_cycle_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleWebhookEvent':
        return cls(
            billing_cycle_id=(str(data.get("billingCycleId", None)) if data.get("billingCycleId", None) is not None else None),
        )


@dataclass(frozen=True)
class Error:
    error_code: Optional[str] = None
    error_description: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['errorCode'] = (self.error_code if self.error_code is not None else None)
        api_dict['errorDescription'] = (self.error_description if self.error_description is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Error':
        return cls(
            error_code=(str(data.get("errorCode", None)) if data.get("errorCode", None) is not None else None),
            error_description=(str(data.get("errorDescription", None)) if data.get("errorDescription", None) is not None else None),
        )


@dataclass(frozen=True)
class LineHealth:
    line_number: str
    """Line number associated with the reservation."""

    checked_at: Optional[datetime.datetime] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['lineNumber'] = self.line_number
        api_dict['checkedAt'] = (self.checked_at.isoformat() if self.checked_at is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'LineHealth':
        return cls(
            line_number=str(data.get("lineNumber", None)),
            checked_at=(dateutil.parser.parse(data.get("checkedAt", None)) if data.get("checkedAt", None) is not None else None),
        )


@dataclass(frozen=True)
class NonrenewableRentalCompact:
    created_at: datetime.datetime
    id: str
    service_name: str
    state: ReservationState
    number: str
    always_on: bool
    sale_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['number'] = self.number
        api_dict['alwaysOn'] = self.always_on
        api_dict['saleId'] = (self.sale_id if self.sale_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'NonrenewableRentalCompact':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            number=str(data.get("number", None)),
            always_on=bool(data.get("alwaysOn", None)),
            sale_id=(str(data.get("saleId", None)) if data.get("saleId", None) is not None else None),
        )


@dataclass(frozen=True)
class NonrenewableRentalUpdateRequest:
    """Supplying a value of 'null' or not supplying a value for any nullable properties will cause the property to be ignored.

    """

    user_notes: Optional[str] = None
    mark_all_sms_read: Optional[bool] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['userNotes'] = (self.user_notes if self.user_notes is not None else None)
        api_dict['markAllSmsRead'] = (self.mark_all_sms_read if self.mark_all_sms_read is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'NonrenewableRentalUpdateRequest':
        return cls(
            user_notes=(str(data.get("userNotes", None)) if data.get("userNotes", None) is not None else None),
            mark_all_sms_read=(bool(data.get("markAllSmsRead", None)) if data.get("markAllSmsRead", None) is not None else None),
        )


@dataclass(frozen=True)
class RefundAction:
    can_refund: bool
    refundable_until: Optional[datetime.datetime] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['canRefund'] = self.can_refund
        api_dict['refundableUntil'] = (self.refundable_until.isoformat() if self.refundable_until is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RefundAction':
        return cls(
            can_refund=bool(data.get("canRefund", None)),
            refundable_until=(dateutil.parser.parse(data.get("refundableUntil", None)) if data.get("refundableUntil", None) is not None else None),
        )


@dataclass(frozen=True)
class RenewableRentalCompact:
    created_at: datetime.datetime
    id: str
    service_name: str
    state: ReservationState
    billing_cycle_id: str
    is_included_for_next_renewal: bool
    number: str
    always_on: bool
    sale_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['billingCycleId'] = self.billing_cycle_id
        api_dict['isIncludedForNextRenewal'] = self.is_included_for_next_renewal
        api_dict['number'] = self.number
        api_dict['alwaysOn'] = self.always_on
        api_dict['saleId'] = (self.sale_id if self.sale_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RenewableRentalCompact':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            billing_cycle_id=str(data.get("billingCycleId", None)),
            is_included_for_next_renewal=bool(data.get("isIncludedForNextRenewal", None)),
            number=str(data.get("number", None)),
            always_on=bool(data.get("alwaysOn", None)),
            sale_id=(str(data.get("saleId", None)) if data.get("saleId", None) is not None else None),
        )


@dataclass(frozen=True)
class RenewableRentalUpdateRequest:
    """Supplying a value of 'null' or not supplying a value for any nullable properties will cause the property to be ignored.

    """

    user_notes: Optional[str] = None
    include_for_renewal: Optional[bool] = None
    mark_all_sms_read: Optional[bool] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['userNotes'] = (self.user_notes if self.user_notes is not None else None)
        api_dict['includeForRenewal'] = (self.include_for_renewal if self.include_for_renewal is not None else None)
        api_dict['markAllSmsRead'] = (self.mark_all_sms_read if self.mark_all_sms_read is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RenewableRentalUpdateRequest':
        return cls(
            user_notes=(str(data.get("userNotes", None)) if data.get("userNotes", None) is not None else None),
            include_for_renewal=(bool(data.get("includeForRenewal", None)) if data.get("includeForRenewal", None) is not None else None),
            mark_all_sms_read=(bool(data.get("markAllSmsRead", None)) if data.get("markAllSmsRead", None) is not None else None),
        )


@dataclass(frozen=True)
class RentalPriceCheckRequest:
    service_name: str
    """Name of the service"""

    area_code: bool
    """Example: True"""

    number_type: NumberType
    capability: ReservationCapability
    always_on: bool
    """Example: True"""

    is_renewable: bool
    """Example: True"""

    duration: RentalDuration
    call_forwarding: Optional[bool] = None
    billing_cycle_id_to_assign_to: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['serviceName'] = self.service_name
        api_dict['areaCode'] = self.area_code
        api_dict['numberType'] = self.number_type.to_api()
        api_dict['capability'] = self.capability.to_api()
        api_dict['alwaysOn'] = self.always_on
        api_dict['isRenewable'] = self.is_renewable
        api_dict['duration'] = self.duration.to_api()
        api_dict['callForwarding'] = (self.call_forwarding if self.call_forwarding is not None else None)
        api_dict['billingCycleIdToAssignTo'] = (self.billing_cycle_id_to_assign_to if self.billing_cycle_id_to_assign_to is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RentalPriceCheckRequest':
        return cls(
            service_name=str(data.get("serviceName", None)),
            area_code=bool(data.get("areaCode", None)),
            number_type=NumberType.from_api(data.get("numberType", None)),
            capability=ReservationCapability.from_api(data.get("capability", None)),
            always_on=bool(data.get("alwaysOn", None)),
            is_renewable=bool(data.get("isRenewable", None)),
            duration=RentalDuration.from_api(data.get("duration", None)),
            call_forwarding=(bool(data.get("callForwarding", None)) if data.get("callForwarding", None) is not None else None),
            billing_cycle_id_to_assign_to=(str(data.get("billingCycleIdToAssignTo", None)) if data.get("billingCycleIdToAssignTo", None) is not None else None),
        )


@dataclass(frozen=True)
class WebhookEventReservationCreatedWebhookEvent:
    attempt: int
    """Send attempt count"""

    occurred_at: datetime.datetime
    """When the event occurred"""

    data: ReservationCreatedWebhookEvent
    event: str
    """Name of the event"""

    id: str
    """Id of event"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['attempt'] = self.attempt
        api_dict['occurredAt'] = self.occurred_at.isoformat()
        api_dict['data'] = self.data.to_api()
        api_dict['event'] = self.event
        api_dict['id'] = self.id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WebhookEventReservationCreatedWebhookEvent':
        return cls(
            attempt=int(data.get("attempt", None)),
            occurred_at=dateutil.parser.parse(data.get("occurredAt", None)),
            data=ReservationCreatedWebhookEvent.from_api(data.get("data", None)),
            event=str(data.get("event", None)),
            id=str(data.get("id", None)),
        )


@dataclass(frozen=True)
class ReuseAction:
    reusable_until: Optional[datetime.datetime] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['reusableUntil'] = (self.reusable_until.isoformat() if self.reusable_until is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReuseAction':
        return cls(
            reusable_until=(dateutil.parser.parse(data.get("reusableUntil", None)) if data.get("reusableUntil", None) is not None else None),
        )


@dataclass(frozen=True)
class Sms:
    """Sms

    """

    id: str
    to_value: str
    created_at: datetime.datetime
    encrypted: bool
    from_value: Optional[str] = None
    sms_content: Optional[str] = None
    parsed_code: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['to'] = self.to_value
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['encrypted'] = self.encrypted
        api_dict['from'] = (self.from_value if self.from_value is not None else None)
        api_dict['smsContent'] = (self.sms_content if self.sms_content is not None else None)
        api_dict['parsedCode'] = (self.parsed_code if self.parsed_code is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Sms':
        return cls(
            id=str(data.get("id", None)),
            to_value=str(data.get("to", None)),
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            encrypted=bool(data.get("encrypted", None)),
            from_value=(str(data.get("from", None)) if data.get("from", None) is not None else None),
            sms_content=(str(data.get("smsContent", None)) if data.get("smsContent", None) is not None else None),
            parsed_code=(str(data.get("parsedCode", None)) if data.get("parsedCode", None) is not None else None),
        )


@dataclass(frozen=True)
class SmsWebhookEvent:
    to_value: str
    created_at: datetime.datetime
    encrypted: bool
    """True if the contents of the sms is encrypted at rest."""

    from_value: Optional[str] = None
    sms_content: Optional[str] = None
    parsed_code: Optional[str] = None
    reservation_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['to'] = self.to_value
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['encrypted'] = self.encrypted
        api_dict['from'] = (self.from_value if self.from_value is not None else None)
        api_dict['smsContent'] = (self.sms_content if self.sms_content is not None else None)
        api_dict['parsedCode'] = (self.parsed_code if self.parsed_code is not None else None)
        api_dict['reservationId'] = (self.reservation_id if self.reservation_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'SmsWebhookEvent':
        return cls(
            to_value=str(data.get("to", None)),
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            encrypted=bool(data.get("encrypted", None)),
            from_value=(str(data.get("from", None)) if data.get("from", None) is not None else None),
            sms_content=(str(data.get("smsContent", None)) if data.get("smsContent", None) is not None else None),
            parsed_code=(str(data.get("parsedCode", None)) if data.get("parsedCode", None) is not None else None),
            reservation_id=(str(data.get("reservationId", None)) if data.get("reservationId", None) is not None else None),
        )


@dataclass(frozen=True)
class UsageWindowEstimateResponse:
    reservation_id: str
    """Id of the reservation that this usage window estimate is associated with."""

    estimated_window_start: Optional[datetime.datetime] = None
    estimated_window_end: Optional[datetime.datetime] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['reservationId'] = self.reservation_id
        api_dict['estimatedWindowStart'] = (self.estimated_window_start.isoformat() if self.estimated_window_start is not None else None)
        api_dict['estimatedWindowEnd'] = (self.estimated_window_end.isoformat() if self.estimated_window_end is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'UsageWindowEstimateResponse':
        return cls(
            reservation_id=str(data.get("reservationId", None)),
            estimated_window_start=(dateutil.parser.parse(data.get("estimatedWindowStart", None)) if data.get("estimatedWindowStart", None) is not None else None),
            estimated_window_end=(dateutil.parser.parse(data.get("estimatedWindowEnd", None)) if data.get("estimatedWindowEnd", None) is not None else None),
        )


@dataclass(frozen=True)
class WakeResponse:
    id: str
    """The Id of this wake request."""

    is_scheduled: bool
    """Indicates whether or not the wake request was successfully scheduled. If a wake request fails to be scheduled, then you will have to submit a new wake request. Too many wake requests may result in wake request throttling."""

    usage_window_start: Optional[datetime.datetime] = None
    usage_window_end: Optional[datetime.datetime] = None
    reservation_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['id'] = self.id
        api_dict['isScheduled'] = self.is_scheduled
        api_dict['usageWindowStart'] = (self.usage_window_start.isoformat() if self.usage_window_start is not None else None)
        api_dict['usageWindowEnd'] = (self.usage_window_end.isoformat() if self.usage_window_end is not None else None)
        api_dict['reservationId'] = (self.reservation_id if self.reservation_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WakeResponse':
        return cls(
            id=str(data.get("id", None)),
            is_scheduled=bool(data.get("isScheduled", None)),
            usage_window_start=(dateutil.parser.parse(data.get("usageWindowStart", None)) if data.get("usageWindowStart", None) is not None else None),
            usage_window_end=(dateutil.parser.parse(data.get("usageWindowEnd", None)) if data.get("usageWindowEnd", None) is not None else None),
            reservation_id=(str(data.get("reservationId", None)) if data.get("reservationId", None) is not None else None),
        )


@dataclass(frozen=True)
class RentalSnapshot:
    number: str
    renewal_cost: float
    service_name: str
    already_renewed: bool
    included_add_ons: List[AddOnSnapshot]
    excluded_add_ons: List[AddOnSnapshot]

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['number'] = self.number
        api_dict['renewalCost'] = self.renewal_cost
        api_dict['serviceName'] = self.service_name
        api_dict['alreadyRenewed'] = self.already_renewed
        api_dict['includedAddOns'] = [item.to_api() for item in self.included_add_ons]
        api_dict['excludedAddOns'] = [item.to_api() for item in self.excluded_add_ons]
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RentalSnapshot':
        return cls(
            number=str(data.get("number", None)),
            renewal_cost=float(data.get("renewalCost", None)),
            service_name=str(data.get("serviceName", None)),
            already_renewed=bool(data.get("alreadyRenewed", None)),
            included_add_ons=[AddOnSnapshot.from_api(item) for item in data.get("includedAddOns", None)],
            excluded_add_ons=[AddOnSnapshot.from_api(item) for item in data.get("excludedAddOns", None)],
        )


@dataclass(frozen=True)
class WebhookEventBillingCycleWebhookEvent:
    attempt: int
    """Send attempt count"""

    occurred_at: datetime.datetime
    """When the event occurred"""

    data: BillingCycleWebhookEvent
    event: str
    """Name of the event"""

    id: str
    """Id of event"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['attempt'] = self.attempt
        api_dict['occurredAt'] = self.occurred_at.isoformat()
        api_dict['data'] = self.data.to_api()
        api_dict['event'] = self.event
        api_dict['id'] = self.id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WebhookEventBillingCycleWebhookEvent':
        return cls(
            attempt=int(data.get("attempt", None)),
            occurred_at=dateutil.parser.parse(data.get("occurredAt", None)),
            data=BillingCycleWebhookEvent.from_api(data.get("data", None)),
            event=str(data.get("event", None)),
            id=str(data.get("id", None)),
        )


@dataclass(frozen=True)
class NewRentalRequest:
    allow_back_order_reservations: bool
    """If set to true, a rental back order will be created if the requested rental is out of stock"""

    always_on: bool
    """If set to true, a line that does not require wake up will be assigned if in stock"""

    duration: RentalDuration
    is_renewable: bool
    number_type: NumberType
    service_name: str
    """Name of the service"""

    capability: ReservationCapability
    area_code_select_option: Optional[List[str]] = None
    billing_cycle_id_to_assign_to: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['allowBackOrderReservations'] = self.allow_back_order_reservations
        api_dict['alwaysOn'] = self.always_on
        api_dict['duration'] = self.duration.to_api()
        api_dict['isRenewable'] = self.is_renewable
        api_dict['numberType'] = self.number_type.to_api()
        api_dict['serviceName'] = self.service_name
        api_dict['capability'] = self.capability.to_api()
        api_dict['areaCodeSelectOption'] = ([item for item in self.area_code_select_option] if self.area_code_select_option is not None else None)
        api_dict['billingCycleIdToAssignTo'] = (self.billing_cycle_id_to_assign_to if self.billing_cycle_id_to_assign_to is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'NewRentalRequest':
        return cls(
            allow_back_order_reservations=bool(data.get("allowBackOrderReservations", None)),
            always_on=bool(data.get("alwaysOn", None)),
            duration=RentalDuration.from_api(data.get("duration", None)),
            is_renewable=bool(data.get("isRenewable", None)),
            number_type=NumberType.from_api(data.get("numberType", None)),
            service_name=str(data.get("serviceName", None)),
            capability=ReservationCapability.from_api(data.get("capability", None)),
            area_code_select_option=([str(item) for item in data.get("areaCodeSelectOption", None)] if data.get("areaCodeSelectOption", None) is not None else None),
            billing_cycle_id_to_assign_to=(str(data.get("billingCycleIdToAssignTo", None)) if data.get("billingCycleIdToAssignTo", None) is not None else None),
        )


@dataclass(frozen=True)
class NewVerificationRequest:
    service_name: str
    """Example: abra"""

    capability: ReservationCapability
    area_code_select_option: Optional[List[str]] = None
    carrier_select_option: Optional[List[str]] = None
    service_not_listed_name: Optional[str] = None
    max_price: Optional[float] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['serviceName'] = self.service_name
        api_dict['capability'] = self.capability.to_api()
        api_dict['areaCodeSelectOption'] = ([item for item in self.area_code_select_option] if self.area_code_select_option is not None else None)
        api_dict['carrierSelectOption'] = ([item for item in self.carrier_select_option] if self.carrier_select_option is not None else None)
        api_dict['serviceNotListedName'] = (self.service_not_listed_name if self.service_not_listed_name is not None else None)
        api_dict['maxPrice'] = (self.max_price if self.max_price is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'NewVerificationRequest':
        return cls(
            service_name=str(data.get("serviceName", None)),
            capability=ReservationCapability.from_api(data.get("capability", None)),
            area_code_select_option=([str(item) for item in data.get("areaCodeSelectOption", None)] if data.get("areaCodeSelectOption", None) is not None else None),
            carrier_select_option=([str(item) for item in data.get("carrierSelectOption", None)] if data.get("carrierSelectOption", None) is not None else None),
            service_not_listed_name=(str(data.get("serviceNotListedName", None)) if data.get("serviceNotListedName", None) is not None else None),
            max_price=(float(data.get("maxPrice", None)) if data.get("maxPrice", None) is not None else None),
        )


@dataclass(frozen=True)
class NonrenewableRentalExpanded:
    created_at: datetime.datetime
    ends_at: datetime.datetime
    id: str
    refund: RefundAction
    service_name: str
    state: ReservationState
    number: str
    always_on: bool
    sale_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['endsAt'] = self.ends_at.isoformat()
        api_dict['id'] = self.id
        api_dict['refund'] = self.refund.to_api()
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['number'] = self.number
        api_dict['alwaysOn'] = self.always_on
        api_dict['saleId'] = (self.sale_id if self.sale_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'NonrenewableRentalExpanded':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            ends_at=dateutil.parser.parse(data.get("endsAt", None)),
            id=str(data.get("id", None)),
            refund=RefundAction.from_api(data.get("refund", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            number=str(data.get("number", None)),
            always_on=bool(data.get("alwaysOn", None)),
            sale_id=(str(data.get("saleId", None)) if data.get("saleId", None) is not None else None),
        )


@dataclass(frozen=True)
class RenewableRentalExpanded:
    created_at: datetime.datetime
    id: str
    refund: RefundAction
    service_name: str
    state: ReservationState
    billing_cycle_id: str
    is_included_for_next_renewal: bool
    number: str
    always_on: bool
    sale_id: Optional[str] = None

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['refund'] = self.refund.to_api()
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['billingCycleId'] = self.billing_cycle_id
        api_dict['isIncludedForNextRenewal'] = self.is_included_for_next_renewal
        api_dict['number'] = self.number
        api_dict['alwaysOn'] = self.always_on
        api_dict['saleId'] = (self.sale_id if self.sale_id is not None else None)
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'RenewableRentalExpanded':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            refund=RefundAction.from_api(data.get("refund", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            billing_cycle_id=str(data.get("billingCycleId", None)),
            is_included_for_next_renewal=bool(data.get("isIncludedForNextRenewal", None)),
            number=str(data.get("number", None)),
            always_on=bool(data.get("alwaysOn", None)),
            sale_id=(str(data.get("saleId", None)) if data.get("saleId", None) is not None else None),
        )


@dataclass(frozen=True)
class ReservationSaleExpanded:
    created_at: datetime.datetime
    id: str
    back_order_reservations: List[BackOrderReservationCompact]
    reservations: List[Reservation]
    state: ReservationSaleState
    total: float
    updated_at: datetime.datetime

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['backOrderReservations'] = [item.to_api() for item in self.back_order_reservations]
        api_dict['reservations'] = [item.to_api() for item in self.reservations]
        api_dict['state'] = self.state.to_api()
        api_dict['total'] = self.total
        api_dict['updatedAt'] = self.updated_at.isoformat()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ReservationSaleExpanded':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            back_order_reservations=[BackOrderReservationCompact.from_api(item) for item in data.get("backOrderReservations", None)],
            reservations=[Reservation.from_api(item) for item in data.get("reservations", None)],
            state=ReservationSaleState.from_api(data.get("state", None)),
            total=float(data.get("total", None)),
            updated_at=dateutil.parser.parse(data.get("updatedAt", None)),
        )


@dataclass(frozen=True)
class VerificationExpanded:
    number: str
    created_at: datetime.datetime
    ends_at: datetime.datetime
    id: str
    cancel: CancelAction
    reactivate: ReactivationAction
    report: ReportAction
    reuse: ReuseAction
    service_name: str
    state: ReservationState
    total_cost: float

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['number'] = self.number
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['endsAt'] = self.ends_at.isoformat()
        api_dict['id'] = self.id
        api_dict['cancel'] = self.cancel.to_api()
        api_dict['reactivate'] = self.reactivate.to_api()
        api_dict['report'] = self.report.to_api()
        api_dict['reuse'] = self.reuse.to_api()
        api_dict['serviceName'] = self.service_name
        api_dict['state'] = self.state.to_api()
        api_dict['totalCost'] = self.total_cost
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'VerificationExpanded':
        return cls(
            number=str(data.get("number", None)),
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            ends_at=dateutil.parser.parse(data.get("endsAt", None)),
            id=str(data.get("id", None)),
            cancel=CancelAction.from_api(data.get("cancel", None)),
            reactivate=ReactivationAction.from_api(data.get("reactivate", None)),
            report=ReportAction.from_api(data.get("report", None)),
            reuse=ReuseAction.from_api(data.get("reuse", None)),
            service_name=str(data.get("serviceName", None)),
            state=ReservationState.from_api(data.get("state", None)),
            total_cost=float(data.get("totalCost", None)),
        )


@dataclass(frozen=True)
class WebhookEventSmsWebhookEvent:
    attempt: int
    """Send attempt count"""

    occurred_at: datetime.datetime
    """When the event occurred"""

    data: SmsWebhookEvent
    event: str
    """Name of the event"""

    id: str
    """Id of event"""


    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['attempt'] = self.attempt
        api_dict['occurredAt'] = self.occurred_at.isoformat()
        api_dict['data'] = self.data.to_api()
        api_dict['event'] = self.event
        api_dict['id'] = self.id
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'WebhookEventSmsWebhookEvent':
        return cls(
            attempt=int(data.get("attempt", None)),
            occurred_at=dateutil.parser.parse(data.get("occurredAt", None)),
            data=SmsWebhookEvent.from_api(data.get("data", None)),
            event=str(data.get("event", None)),
            id=str(data.get("id", None)),
        )


@dataclass(frozen=True)
class BillingCycleRenewalInvoice:
    created_at: datetime.datetime
    id: str
    excluded_rentals: List[RentalSnapshot]
    included_rentals: List[RentalSnapshot]
    is_paid_for: bool
    total_cost: float

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['createdAt'] = self.created_at.isoformat()
        api_dict['id'] = self.id
        api_dict['excludedRentals'] = [item.to_api() for item in self.excluded_rentals]
        api_dict['includedRentals'] = [item.to_api() for item in self.included_rentals]
        api_dict['isPaidFor'] = self.is_paid_for
        api_dict['totalCost'] = self.total_cost
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleRenewalInvoice':
        return cls(
            created_at=dateutil.parser.parse(data.get("createdAt", None)),
            id=str(data.get("id", None)),
            excluded_rentals=[RentalSnapshot.from_api(item) for item in data.get("excludedRentals", None)],
            included_rentals=[RentalSnapshot.from_api(item) for item in data.get("includedRentals", None)],
            is_paid_for=bool(data.get("isPaidFor", None)),
            total_cost=float(data.get("totalCost", None)),
        )


@dataclass(frozen=True)
class BillingCycleRenewalInvoicePreview:
    billing_cycle_id: str
    renewal_estimate: BillingCycleRenewalInvoice

    def to_api(self) -> Dict[str, Any]:
        api_dict = dict()
        api_dict['billingCycleId'] = self.billing_cycle_id
        api_dict['renewalEstimate'] = self.renewal_estimate.to_api()
        return api_dict

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'BillingCycleRenewalInvoicePreview':
        return cls(
            billing_cycle_id=str(data.get("billingCycleId", None)),
            renewal_estimate=BillingCycleRenewalInvoice.from_api(data.get("renewalEstimate", None)),
        )


