from enum import Enum


class TestMode(Enum):
    """Live operation and server-backed Phoneblur test scenarios.

    Each value is the documented ``test_*`` service name understood by the
    Phoneblur API. Use a scenario only with the verification or rental routes
    that support it.
    """

    LIVE = "live"
    MOCK_SUCCESS = "test_success"
    MOCK_RENEWABLE_EXPIRED = "test_renewable_expired"
    MOCK_NONRENEWABLE_EXPIRED = "test_nonrenewable_expired"
    MOCK_DELAYED_SUCCESS = "test_delayed_success"
    MOCK_PENDING = "test_pending"
    MOCK_INSUFFICIENT_BALANCE = "test_insufficient_balance"
    MOCK_NO_NUMBERS = "test_no_numbers"
    MOCK_TOO_MANY_UNFINISHED_VERIFICATIONS = "test_too_many_unfinished_verifications"
    MOCK_TIMEOUT = "test_timeout"
    MOCK_REACTIVATABLE = "test_reactivatable"
    MOCK_BACKORDER = "test_backorder"

    __test__ = False


def normalize_test_mode(value):
    """Return a valid test mode or ``None`` to inherit a parent setting."""
    if value is None or isinstance(value, TestMode):
        return value

    raise ValueError("test mode must be a TestMode value or None.")
