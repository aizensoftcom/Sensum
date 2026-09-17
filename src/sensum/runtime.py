from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from .attention import AttentionPolicy, ThresholdAttention
from .bus import EventBus
from .models import SensoryEvent
from .sensors.base import Sensor
from .world import WorldState


@dataclass(slots=True)
class RuntimeStats:
    observed: int = 0
    emitted: int = 0
    suppressed: int = 0
    sensor_errors: int = 0


class SensumRuntime:
    """Orchestrates sensors, attention gating, world-state updates and event delivery."""

    def __init__(
        self,
        *,
        attention: AttentionPolicy | None = None,
        world: WorldState | None = None,
    ) -> None:
        self.attention = attention or ThresholdAttention()
        self.world = world or WorldState()
        self.bus = EventBus()
        self.stats = RuntimeStats()
        self._sensors: list[Sensor] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._running = False

    def add_sensor(self, sensor: Sensor) -> SensumRuntime:
        if self._running:
            raise RuntimeError("cannot add sensors after runtime has started")
        self._sensors.append(sensor)
        return self

    async def ingest(self, event: SensoryEvent) -> bool:
        self.stats.observed += 1
        self.world.apply(event)
        decision = self.attention.assess(event)
        event.metadata.setdefault(
            "attention",
            {
                "score": round(decision.score, 5),
                "significant": decision.significant,
                "reasons": list(decision.reasons),
            },
        )
        if not decision.significant:
            self.stats.suppressed += 1
            return False
        self.stats.emitted += 1
        await self.bus.publish(event)
        return True

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tasks = [
            asyncio.create_task(self._run_sensor(sensor), name=f"sensum:{sensor.name}")
            for sensor in self._sensors
        ]

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def events(self) -> AsyncIterator[SensoryEvent]:
        async for event in self.bus.subscribe():
            yield event

    async def _run_sensor(self, sensor: Sensor) -> None:
        try:
            async for event in sensor.events():
                if not self._running:
                    break
                await self.ingest(event)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - sensor boundary isolates third-party failures
            self.stats.sensor_errors += 1
