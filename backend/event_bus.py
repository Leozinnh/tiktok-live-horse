import asyncio
from typing import Dict, List, Callable, Any, Awaitable

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self._all_subscribers: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running: bool = False

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        self._all_subscribers.append(callback)

    async def publish(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type", "")
        # Notifica listeners específicos
        if event_type in self._subscribers:
            for cb in self._subscribers[event_type]:
                try:
                    res = cb(event)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    print(f"Erro no subscriber de {event_type}: {e}")
                    
        # Notifica listeners gerais
        for cb in self._all_subscribers:
            try:
                res = cb(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                print(f"Erro no subscriber geral: {e}")
