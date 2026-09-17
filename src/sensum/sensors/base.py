from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from sensum.models import SensoryEvent


@dataclass(slots=True)
class SensorStats:
    """Counters collected before events reach the central attention gate."""

    raw_observations: int = 0
    semantic_events: int = 0

    @property
    def local_reduction_ratio(self) -> float:
        if self.raw_observations == 0:
            return 0.0
        return 1.0 - (self.semantic_events / self.raw_observations)


class Sensor(Protocol):
    """A source of semantic sensory events."""

    name: str

    def events(self) -> AsyncIterator[SensoryEvent]: ...
