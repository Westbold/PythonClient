from enum import Enum


class TestMode(Enum):
    """Server-backed Phoneblur test scenarios.

    Each value is the documented ``test_*`` service name understood by the
    Phoneblur API. Use a scenario only with the verification or rental routes
    that support it.
    """

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


class _InheritedTestMode:
    def __repr__(self):
        return "INHERIT_TEST_MODE"


INHERIT_TEST_MODE = _InheritedTestMode()


def normalize_test_mode(value, allow_inherit=False):
    """Return a valid test mode, ``None``, or the inheritance sentinel."""
    if value is INHERIT_TEST_MODE:
        if allow_inherit:
            return value
        raise ValueError("test mode cannot inherit in this context.")

    if value is None or isinstance(value, TestMode):
        return value

    raise ValueError("test mode must be a TestMode value or None.")
