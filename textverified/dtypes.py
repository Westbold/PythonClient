from dataclasses import dataclass
from enum import Enum
import datetime
from typing import Optional

@dataclass(frozen=True)
class AreaCode:
    area_code: str
    state: str

@dataclass(frozen=True)
class SMS:
    from_number: Optional[str]
    to_number: str
    created_at: datetime.datetime
    sms_content: Optional[str]
    parsed_code: Optional[str]
    encrypted: bool

class NumberType(Enum):
    MOBILE = "mobile"
    VOIP = "voip"
    LANDLINE = "landline"

    @classmethod
    def from_string(cls, type_str: str) -> 'NumberType':
        if type_str.lower() == "mobile":
            return cls.MOBILE
        elif type_str.lower() == "voip":
            return cls.VOIP
        elif type_str.lower() == "landline":
            return cls.LANDLINE
        else:
            raise ValueError(f"Unknown number type: {type_str}")
        
    def __str__(self) -> str:
        return self.value

class ReservationType(Enum):
    """Enum representing reservation types."""
    RENEWABLE = "renewable"
    NON_RENEWABLE = "nonrenewable"
    VERIFICATION = "verification"

    @classmethod
    def from_string(cls, type_str: str) -> 'ReservationType':
        if type_str.lower() == "renewable":
            return cls.RENEWABLE
        elif type_str.lower() == "nonrenewable":
            return cls.NON_RENEWABLE
        elif type_str.lower() == "verification":
            return cls.VERIFICATION
        else:
            raise ValueError(f"Unknown reservation type: {type_str}")

    def __str__(self) -> str:
        return self.value

class LineStatus(Enum):
    """Enum representing the status of a line, either renewable, non-renewable, or verification."""
    # This may not be the best way to represent this. It mirrors api behavior (list verifications, list renewable/non-)
    # However, it may be better to split into RentalStatus and VerificationStatus and use tuple keys (ReservationType, Status)
    # Yet, it may be beneficial to have a single enum that mirrors API behavior IF a LineStatus is ever used as an input (which it currently is not)
    VERIFICATION_PENDING = "verificationPending"
    VERIFICATION_COMPLETED = "verificationCompleted"
    VERIFICATION_CANCELED = "verificationCanceled"
    VERIFICATION_TIMED_OUT = "verificationTimedOut"
    VERIFICATION_REPORTED = "verificationReported"
    VERIFICATION_REFUNDED = "verificationRefunded"
    VERIFICATION_REUSED = "verificationReused"
    VERIFICATION_REACTIVATED = "verificationReactivated"

    RENEWABLE_ACTIVE = "renewableActive"
    RENEWABLE_OVERDUE = "renewableOverdue"
    RENEWABLE_EXPIRED = "renewableExpired"
    RENEWABLE_REFUNDED = "renewableRefunded"

    NON_RENEWABLE_ACTIVE = "nonRenewableActive"
    NON_RENEWABLE_EXPIRED = "nonRenewableExpired"
    NON_RENEWABLE_REFUNDED = "nonRenewableRefunded"

    def __str__(self) -> str:
        return self.value

class RentalDuration(Enum):
    """Enum representing duration options for rentals."""
    ONE_DAY = datetime.timedelta(days=1)
    THREE_DAYS = datetime.timedelta(days=3)
    SEVEN_DAYS = datetime.timedelta(days=7)
    FOURTEEN_DAYS = datetime.timedelta(days=14)
    THIRTY_DAYS = datetime.timedelta(days=30)
    NINETY_DAYS = datetime.timedelta(days=90)
    ONE_YEAR = datetime.timedelta(days=365)

    # This is never returned by the API, so no need for a from_string method.
    
    @classmethod
    def from_timedelta(cls, duration: datetime.timedelta) -> 'RentalDuration':
        for option in cls:
            if option.value == duration:
                return option
        raise ValueError(f"Unknown rental duration: {duration}")
    
    def __str__(self) -> str:
        if self == self.ONE_DAY:
            return "oneDay"
        elif self == self.THREE_DAYS:
            return "threeDay"
        elif self == self.SEVEN_DAYS:
            return "sevenDay"
        elif self == self.FOURTEEN_DAYS:
            return "fourteenDay"
        elif self == self.THIRTY_DAYS:
            return "thirtyDay"
        elif self == self.NINETY_DAYS:
            return "ninetyDay"
        elif self == self.ONE_YEAR:
            return "oneYear"
        else:
            raise ValueError(f"Unknown rental duration: {self}")

class Capability(Enum):
    """Enum represenging the capabilities of a phone number."""
    SMS = 0b01
    VOICE = 0b10
    SMS_AND_VOICE = SMS | VOICE

    @classmethod
    def from_string(cls, capability_str: str) -> 'Capability':
        if capability_str.lower() == "sms":
            return cls.SMS
        elif capability_str.lower() == "voice":
            return cls.VOICE
        elif capability_str.lower() == "smsandvoicecombo":
            return cls.SMS_AND_VOICE
        else:
            raise ValueError(f"Unknown capability: {capability_str}")
        
    def __str__(self) -> str:
        if self == self.SMS:
            return "sms"
        elif self == self.VOICE:
            return "voice"
        elif self == self.SMS_AND_VOICE:
            return "smsAndVoiceCombo"
        else:
            raise ValueError(f"Unknown capability: {self}")
        
class SaleState(Enum):
    """Enum representing the status of a sale."""
    CREATED = "created"
    PROCESSING = "processing"
    FAILED = "failed"
    SUCCEEDED = "succeeded"

    @classmethod
    def from_string(cls, state_str: str) -> 'SaleState':
        if state_str.lower() == "created":
            return cls.CREATED
        elif state_str.lower() == "processing":
            return cls.PROCESSING
        elif state_str.lower() == "failed":
            return cls.FAILED
        elif state_str.lower() == "succeeded":
            return cls.SUCCEEDED
        else:
            raise ValueError(f"Unknown sale state: {state_str}")
        
    def __str__(self) -> str:
        return self.value
    
class BillingCycleState(Enum):
    """Enum representing the billing cycle state."""
    # Currently, this guarantee is provided by the code but not by the API docs.
    # TODO: actually test this. Thoroughly. Especially the SUSPENDED_FOR_FRAUD state.
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED_FOR_FRAUD = "Suspended_For_Fraud"

    @classmethod
    def from_string(cls, state_str: str) -> 'BillingCycleState':
        if state_str.lower() == "active":
            return cls.ACTIVE
        elif state_str.lower() == "expired":
            return cls.EXPIRED
        elif state_str.lower() == "suspended_for_fraud":
            return cls.SUSPENDED_FOR_FRAUD
        else:
            raise ValueError(f"Unknown billing cycle state: {state_str}")
        
    def __str__(self) -> str:
        return self.value