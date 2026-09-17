from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .attention import AttentionPolicy, ThresholdAttention
from .bus import EventBus
from .fusion import TemporalFusionEngine
from .models import SensoryEvent
from .sensors.base import Sensor
from .trace import TraceBuffer
from .world import WorldState


class EventStore(Protocol):
    def append(self, event: SensoryEvent) -> int: ...

    def count(self) -> int: ...


@dataclass(slots=True)
class RuntimeStats:
    observed: int = 0
    emitted: int = 0
    suppressed: int = 0
    fused: int = 0
    persisted: int = 0
    sensor_errors: int = 0


class SensumRuntime:
    """Orchestrates sensors, state, persistence, fusion, attention and delivery."""

    def __init__(
        self,
        *,
        attention: AttentionPolicy | None = None,
        world: WorldState | None = None,
        store: EventStore | None = None,
        fusion: TemporalFusionEngine | None = None,
        trace: TraceBuffer | None = None,
    ) -> None:
        self.attention = attention or ThresholdAttention()
        self.world = world or WorldState()
        self.store = store
        self.fusion = fusion
        self.trace = trace or TraceBuffer()
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
        emitted = await self._process(event, allow_fusion=True)
        return emitted

    async def _process(self, event: SensoryEvent, *, allow_fusion: bool) -> bool:
        self.stats.observed += 1
        self.world.apply(event)

        persisted = self.store is not None
        if self.store is not None:
            self.store.append(event)
            self.stats.persisted += 1

        decision = self.attention.assess(event)
        event.metadata.setdefault(
            "attention",
            {
                "score": round(decision.score, 5),
                "significant": decision.significant,
                "reasons": list(decision.reasons),
            },
        )

        emitted = False
        if not decision.significant:
            self.stats.suppressed += 1
        else:
            self.stats.emitted += 1
            emitted = True
            await self.bus.publish(event)

        self.trace.record(
            event,
            attention_score=decision.score,
            significant=decision.significant,
            attention_reasons=decision.reasons,
            persisted=persisted,
            published=emitted,
        )

        if allow_fusion and self.fusion is not None:
            for fused in self.fusion.observe(event):
                self.stats.fused += 1
                await self._process(fused, allow_fusion=False)

        return emitted

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

    def metrics(self) -> dict[str, Any]:
        sensors: dict[str, dict[str, Any]] = {}
        raw_total = 0
        semantic_total = 0

        for sensor in self._sensors:
            stats = getattr(sensor, "stats", None)
            if stats is None:
                continue
            raw = int(getattr(stats, "raw_observations", 0))
            semantic = int(getattr(stats, "semantic_events", 0))
            raw_total += raw
            semantic_total += semantic
            sensors[sensor.name] = {
                "raw_observations": raw,
                "semantic_events": semantic,
                "local_reduction_ratio": round(
                    float(getattr(stats, "local_reduction_ratio", 0.0)), 6
                ),
            }

        reasoning_reduction = 0.0
        if raw_total:
            reasoning_reduction = 1.0 - (self.stats.emitted / raw_total)

        return {
            "runtime": asdict(self.stats),
            "sensors": sensors,
            "totals": {
                "raw_observations": raw_total,
                "semantic_events": semantic_total,
                "reasoning_events": self.stats.emitted,
                "reasoning_reduction_ratio": round(reasoning_reduction, 6),
                "persisted_events": self.store.count() if self.store is not None else 0,
                "perception_traces": len(self.trace),
            },
        }

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
