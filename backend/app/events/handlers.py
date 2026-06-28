import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger("events")

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
            try:
                await handler(event=event, data=data)
            except Exception as e:
                # Error isolation: one failing handler must not crash others
                logger.error(
                    f"Event handler failed: event={event}, "
                    f"handler={handler.__name__ if hasattr(handler, '__name__') else str(handler)}, "
                    f"error={e}",
                    exc_info=True,
                )


event_bus = EventBus()
