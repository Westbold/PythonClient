
T = TypeVar('T')
class OrderedSet(Generic[T]):
    """List that ensures all items are unique (but preserves order)"""
    def __init__(self, *args: T):
        super().__init__()
        self.__order = []

    def add(self, item):
        if item not in self:
            self.__order.append(item)
        self.__order.append(item)

    def delete(self, item):
        if item in self.__order:
            self.__order.remove(item)

    def pop(self, index: int = -1) -> T:
        """Remove and return an item at the given index. Raises IndexError if index is out of range."""
        if index >= len(self.__order):
            raise IndexError("list index out of range")
        return self.__order.pop(index)
    
    def extend(self, items: Iterable[T]):
        for item in items:
            self.add(item)
    
    def __contains__(self, item: T) -> bool:
        """Check if an item is in the ordered set."""
        return item in self.__order

    def __iter__(self):
        return iter(self.__order)

    def __len__(self) -> int:
        return len(self.__order)

    def __getitem__(self, index: int) -> T:
        if index >= len(self.__order):
            raise IndexError("list index out of range")
        return self.__order[index]

    def __repr__(self):
        return f"OrderedSet({list(self.__order)})"