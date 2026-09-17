from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sensum.models import Modality, SensoryEvent, StateChange

from .base import SensorStats


class DemoSensor:
    """Scripted privacy-safe semantic events for the zero-config Sensum demo.

    This sensor exists to explain the runtime, not to produce benchmark claims.
    """

    name = "demo"

    def __init__(self, *, interval: float = 0.8, repeat: bool = True) -> None:
        if interval <= 0:
            raise ValueError("interval must be > 0")
        self.interval = interval
        self.repeat = repeat
        self.stats = SensorStats()

    async def events(self) -> AsyncIterator[SensoryEvent]:
        while True:
            for event in self._script():
                self.stats.raw_observations += 1
                self.stats.semantic_events += 1
                yield event
                await asyncio.sleep(self.interval)
            if not self.repeat:
                return
            await asyncio.sleep(self.interval * 2)

    def _script(self) -> list[SensoryEvent]:
        return [
            SensoryEvent(
                kind="ambient.noise",
                source=self.name,
                modality=Modality.AUDIO,
                summary="Low-value background audio activity",
                confidence=0.96,
                novelty=0.04,
                urgency=0.01,
                tags=["demo", "noise"],
            ),
            SensoryEvent(
                kind="speech.started",
                source=self.name,
                modality=Modality.AUDIO,
                summary="User started speaking",
                entity="user:demo",
                confidence=0.98,
                novelty=0.30,
                urgency=0.10,
                tags=["demo", "speech"],
            ),
            SensoryEvent(
                kind="browser.navigated",
                source=self.name,
                modality=Modality.BROWSER,
                summary="Browser moved from product page to checkout",
                entity="browser:demo",
                changes=[StateChange("url", "/product", "/checkout")],
                confidence=0.99,
                novelty=0.78,
                urgency=0.28,
                tags=["demo", "browser"],
            ),
            SensoryEvent(
                kind="browser.changed",
                source=self.name,
                modality=Modality.BROWSER,
                summary="Minor layout churn with no meaningful state change",
                entity="browser:demo",
                confidence=0.94,
                novelty=0.08,
                urgency=0.01,
                tags=["demo", "noise"],
            ),
            SensoryEvent(
                kind="user.interrupted_agent",
                source=self.name,
                modality=Modality.AUDIO,
                summary="User intentionally interrupted while the agent was speaking",
                entity="conversation:demo",
                confidence=0.99,
                novelty=0.97,
                urgency=0.95,
                tags=["demo", "interrupt", "important"],
            ),
            SensoryEvent(
                kind="payment.completed",
                source=self.name,
                modality=Modality.API,
                summary="Payment status changed from pending to completed",
                entity="payment:demo",
                changes=[StateChange("status", "pending", "completed")],
                confidence=0.99,
                novelty=0.98,
                urgency=0.88,
                tags=["demo", "payment", "important"],
            ),
        ]
