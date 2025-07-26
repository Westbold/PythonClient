from typing import Generic, TypeVar, Callable, Iterator, Optional, List
from .action import _Action, _ActionPerformer

T = TypeVar('T')
class PaginatedList(Generic[T], Iterator[T]):

    # Consider supporting a union of paginated lists (to allow for returning all renewable and non-renewable reservations in one method call)
    
    def __init__(self, request_json:dict, parse_item: Callable[[dict], T], api_context: _ActionPerformer):
        self.parse_item = parse_item
        self.api_context = api_context

        self.__items = [self.parse_item(item) for item in request_json.get("data", [])]
        self.__set_next_page(request_json)
        self.__current_index = 0

    def __iter__(self) -> Iterator[T]:
        """Make the PaginatedList iterable."""
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

    def __getitem__(self, index: int) -> T:
        """Get item by index, fetching pages as needed."""
        # If requesting an index beyond current items and there's a next page
        while index >= len(self.__items) and self.__next_page is not None:
            self._fetch_next_page()
        
        if index >= len(self.__items):
            raise IndexError("list index out of range")
        
        return self.__items[index]

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
        print("Current page set to:", current_page)
        print(f"Next page set to: {self.__next_page}")
        
    def get_all_items(self) -> List[T]:
        """Fetch all remaining pages and return all items."""
        while self.__next_page is not None:
            self._fetch_next_page()
        return self.__items.copy()
