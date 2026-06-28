from typing import Any, Callable, Dict, List

EventHandler = Callable[..., Any]


class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event: str, handler: EventHandler) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        if event in self._handlers:
            self._handlers[event].remove(handler)

    async def publish(self, event: str, **data: Any) -> None:
        handlers = self._handlers.get(event, [])
        for handler in handlers:
            await handler(event=event, data=data)


event_bus = EventBus()
