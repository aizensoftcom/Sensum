from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .models import SensoryEvent


class EventBus:
    """In-process fan-out bus for significant sensory events."""

    def __init__(self, queue_size: int = 256) -> None:
        self._queue_size = queue_size
        self._subscribers: set[asyncio.Queue[SensoryEvent]] = set()

    async def publish(self, event: SensoryEvent) -> None:
        for queue in tuple(self._subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[SensoryEvent]:
        queue: asyncio.Queue[SensoryEvent] = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)
