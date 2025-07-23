from dataclasses import dataclass
from typing import Any, Dict, Union, Protocol
from requests.structures import CaseInsensitiveDict


@dataclass(frozen=True)
class _ActionResponse:
    """Internal Protocol for API responses."""
    
    data: Any
    headers: CaseInsensitiveDict[str, Union[str, int]]

class _ActionPerformer(Protocol):
    """Internal Protocol for objects that can perform API actions."""
    
    def _perform_action(self, action: '_Action') -> _ActionResponse:
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

    @staticmethod
    def from_dict(data: dict) -> '_Action':
        """
        Create an Action instance from a dictionary.
        :param data: Dictionary containing action details.
        :return: Action instance.
        """
        if not isinstance(data, dict) or "method" not in data or "href" not in data:
            raise ValueError("Invalid data for Action creation. Must be a dictionary containing 'method' and 'href'.")
        
        return _Action(method=data.get("method"), href=data.get("href"))

    def to_dict(self) -> dict:
        """
        Convert the Action instance to a dictionary.
        :return: Dictionary representation of the Action.
        """
        return {
            "method": self.method,
            "href": self.href
        }