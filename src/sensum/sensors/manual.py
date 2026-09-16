from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sensum.models import SensoryEvent


class ManualSensor:
    """Queue-backed sensor useful for SDK integrations and tests."""

    def __init__(self, name: str = "manual") -> None:
        self.name = name
        self._queue: asyncio.Queue[SensoryEvent | None] = asyncio.Queue()

    async def emit(self, event: SensoryEvent) -> None:
        await self._queue.put(event)

    async def close(self) -> None:
        await self._queue.put(None)

    async def events(self) -> AsyncIterator[SensoryEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event
