from dataclasses import dataclass
from typing import Any, Dict, Union
from requests.structures import CaseInsensitiveDict


@dataclass(frozen=True)
class _ActionResponse:
    """Internal Protocol for API responses."""

    data: Any
    headers: "CaseInsensitiveDict[str, Union[str, int]]"


class _ActionPerformer:
    """Internal Protocol for objects that can perform API actions."""

    def _perform_action(self, action: "_Action", **kwargs) -> _ActionResponse:
        """
        Perform an API action and return the result.
        :param action: The action to perform
        :return: Dictionary containing the API response
        """
        pass


@dataclass(frozen=True)
class _Action:
    """Single API action. Often returned by the API but also used internally."""

    method: str
    href: str

    def to_api(self) -> dict:
        """
        Convert the Action instance to an API-compatible dictionary.
        :return: Dictionary representation of the Action for API requests.
        """
        return {"method": self.method, "href": self.href}

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "_Action":
        """
        Create an Action instance from API data.
        :param data: Dictionary containing the API data.
        :return: Action instance.
        """
        return cls(method=data["method"], href=data["href"])
