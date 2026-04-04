from collections import OrderedDict
from collections.abc import Generator


class FIFOCache[T]:
    def __init__(self, max_size: int):
        self._max_size = max_size
        self._cache = OrderedDict[T, None]()

    def __contains__(self, item: T) -> bool:
        return item in self._cache

    def __iter__(self) -> Generator[T]:
        for item in self._cache:
            yield item

    def __repr__(self) -> str:
        return f'{{{', '.join(repr(item) for item in self._cache)}}}'

    def add(self, item: T) -> None:
        self._cache[item] = None

        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def discard(self, item: T) -> None:
        self._cache.pop(item, None)
