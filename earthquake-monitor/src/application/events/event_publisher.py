from abc import ABC, abstractmethod
from typing import Any


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: Any) -> None:
        pass


class InMemoryEventPublisher(EventPublisher):
    def __init__(self):
        self._handlers = {}

    def subscribe(self, event_type: type, handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Any) -> None:
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler(event)
