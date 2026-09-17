from __future__ import annotations

from dataclasses import asdict, dataclass

from .runtime import RuntimeStats
from .sensors.base import SensorStats


@dataclass(slots=True, frozen=True)
class PipelineMetrics:
    raw_observations: int
    semantic_events: int
    emitted_to_reasoner: int
    suppressed_by_attention: int

    @classmethod
    def from_stats(cls, sensor: SensorStats, runtime: RuntimeStats) -> PipelineMetrics:
        return cls(
            raw_observations=sensor.raw_observations,
            semantic_events=sensor.semantic_events,
            emitted_to_reasoner=runtime.emitted,
            suppressed_by_attention=runtime.suppressed,
        )

    @property
    def total_reduction_ratio(self) -> float:
        if self.raw_observations == 0:
            return 0.0
        return 1.0 - self.emitted_to_reasoner / self.raw_observations

    def to_dict(self) -> dict[str, int | float]:
        result = asdict(self)
        result["total_reduction_ratio"] = round(self.total_reduction_ratio, 6)
        return result
