from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from sensum.models import Modality, SensoryEvent, StateChange

from .base import SensorStats


@dataclass(slots=True, frozen=True)
class VisionObservation:
    """Cheap local CV output consumed by Sensum instead of raw camera frames."""

    objects: frozenset[str] = frozenset()
    motion_score: float = 0.0
    scene: str | None = None


VisionProvider = Callable[[], Awaitable[VisionObservation]]


class VisionEventSensor:
    """Turn local motion/object observations into compact semantic vision events."""

    def __init__(
        self,
        provider: VisionProvider,
        *,
        interval: float = 0.1,
        motion_threshold: float = 0.25,
        name: str = "vision",
    ) -> None:
        self.provider = provider
        self.interval = interval
        self.motion_threshold = motion_threshold
        self.name = name
        self.stats = SensorStats()
        self._previous: VisionObservation | None = None

    async def events(self) -> AsyncIterator[SensoryEvent]:
        while True:
            current = await self.provider()
            self.stats.raw_observations += 1
            if self._previous is not None:
                for event in self._compare(self._previous, current):
                    self.stats.semantic_events += 1
                    yield event
            self._previous = current
            await asyncio.sleep(self.interval)

    def _compare(
        self, before: VisionObservation, after: VisionObservation
    ) -> list[SensoryEvent]:
        events: list[SensoryEvent] = []
        entered = sorted(after.objects - before.objects)
        left = sorted(before.objects - after.objects)

        for label in entered:
            events.append(
                SensoryEvent(
                    kind="vision.object_entered",
                    source=self.name,
                    modality=Modality.VISION,
                    entity=f"vision:object:{label}",
                    summary=f"Object entered view: {label}",
                    changes=[StateChange("visible", False, True)],
                    confidence=0.9,
                    novelty=0.82,
                    urgency=0.2,
                    metadata={"label": label, "scene": after.scene},
                    tags=["vision", "object", "entered"],
                )
            )
        for label in left:
            events.append(
                SensoryEvent(
                    kind="vision.object_left",
                    source=self.name,
                    modality=Modality.VISION,
                    entity=f"vision:object:{label}",
                    summary=f"Object left view: {label}",
                    changes=[StateChange("visible", True, False)],
                    confidence=0.9,
                    novelty=0.75,
                    urgency=0.15,
                    metadata={"label": label, "scene": after.scene},
                    tags=["vision", "object", "left"],
                )
            )
        if (
            after.motion_score >= self.motion_threshold
            and before.motion_score < self.motion_threshold
        ):
            events.append(
                SensoryEvent(
                    kind="vision.motion_started",
                    source=self.name,
                    modality=Modality.VISION,
                    entity="vision:scene",
                    summary="Meaningful motion started",
                    changes=[StateChange("motion", False, True)],
                    confidence=0.9,
                    novelty=min(1.0, 0.55 + after.motion_score * 0.4),
                    urgency=min(1.0, after.motion_score * 0.5),
                    metadata={"motion_score": after.motion_score, "scene": after.scene},
                    tags=["vision", "motion", "started"],
                )
            )
        return events
