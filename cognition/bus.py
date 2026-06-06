from collections import defaultdict
from typing import Any, Callable


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[Any], None]) -> None:
        self._subscribers[topic].append(callback)

    def publish(self, topic: str, payload: Any) -> None:
        for cb in self._subscribers[topic]:
            cb(payload)
