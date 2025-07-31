from typing import Generic, TypeVar, Callable, Iterator, Optional, List, Union
from .action import _Action, _ActionPerformer

T = TypeVar("T")


class PaginatedList(Generic[T], Iterator[T]):
    """Handles paginated API responses, allowing iteration over items and fetching additional pages as needed.
    You should not need to instantiate this class directly; use the API methods that return it instead.

    Supports iteration and indexing, allowing you to access items as if it were a regular list.
    To exhaust all items, iterate over it using `list(paginated_list)` or call `paginated_list.get_all_items()`.
    """

    # Consider supporting a union of paginated lists (to allow for returning all renewable and non-renewable reservations in one method call)

    def __init__(self, request_json: dict, parse_item: Callable[[dict], T], api_context: _ActionPerformer):
        self.parse_item = parse_item
        self.api_context = api_context

        self.__items = [self.parse_item(item) for item in request_json.get("data", [])]
        self.__set_next_page(request_json)
        self.__current_index = 0

    def __iter__(self) -> Iterator[T]:
        """Iterate over items in the paginated list."""
        self.__current_index = 0
        return self

    def __next__(self) -> T:
        """Get the next item, fetching the next page if necessary."""
        # If we're at the end of current items and there's a next page, fetch it
        if self.__current_index >= len(self.__items) and self.__next_page is not None:
            self._fetch_next_page()

        # If we still don't have items, we're done
        if self.__current_index >= len(self.__items):
            raise StopIteration

        item = self.__items[self.__current_index]
        self.__current_index += 1
        return item

    def __getitem__(self, index: Union[int, slice]) -> T:
        """Get item by index, fetching pages as needed."""
        # Fetch needed pages
        if isinstance(index, slice):
            if index.start is None and index.stop is None:
                # If slice is empty, return all items
                return self.get_all_items()

            # If start or end is negative, we need to consume all items
            if index.start is not None and index.start < 0:
                self.get_all_items()
            elif index.stop is not None and index.stop < 0:
                self.get_all_items()
            else:
                # Fetch pages until we have enough items
                while self.__next_page is not None and (index.stop is None or index.stop > len(self.__items)):
                    self._fetch_next_page()

            # Return the sliced items
            return self.__items[index]

        elif isinstance(index, int):
            if index < 0:
                # Negative indexing - must consume all items
                self.get_all_items()
            else:
                # Fetch needed pages
                while self.__next_page is not None and index >= len(self.__items):
                    self._fetch_next_page()

            if index >= len(self.__items):
                raise IndexError("list index out of range")

            return self.__items[index]

        raise TypeError("Index must be an integer or slice")

    def _fetch_next_page(self) -> None:
        """Fetch the next page of results and append to current items."""
        if self.__next_page is None:
            return

        next_page_json = self.api_context._perform_action(self.__next_page).data

        # Parse next items
        new_items = [self.parse_item(item) for item in next_page_json.get("data", [])]
        self.__items.extend(new_items)
        self.__set_next_page(next_page_json)

    def __set_next_page(self, current_page: dict) -> None:
        """Set the next page action based on the current page response."""
        if not current_page.get("hasNext", False):
            self.__next_page = None

        elif current_page.get("links", {}).get("next", {}):
            self.__next_page = _Action.from_api(current_page["links"]["next"])
            if not self.__next_page.href or not self.__next_page.method:
                self.__next_page = None

    def get_all_items(self) -> List[T]:
        """Get all items in the paginated list, fetching all pages if necessary.

        Returns:
            List[T]: A list of all items in the paginated list.
        """
        while self.__next_page is not None:
            self._fetch_next_page()
        return self.__items.copy()
