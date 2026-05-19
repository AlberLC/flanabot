from collections import OrderedDict
from collections.abc import Generator, Iterable


class FIFOCache[T]:
    def __init__(self, items: Iterable[T] | None = None, max_size: int | None = None):
        self._max_size = max_size
        self._cache = OrderedDict[T, None]()

        if items is not None:
            for item in items:
                self.add(item)

    def __contains__(self, item: T) -> bool:
        return item in self._cache

    def __iter__(self) -> Generator[T]:
        for item in self._cache:
            yield item

    def __len__(self) -> int:
        return len(self._cache)

    def __repr__(self) -> str:
        return f'{{{', '.join(repr(item) for item in self._cache)}}}'

    def add(self, item: T) -> None:
        self._cache[item] = None

        if self._max_size is not None and len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def discard(self, item: T) -> None:
        self._cache.pop(item, None)
