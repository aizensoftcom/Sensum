from __future__ import annotations

import random
from dataclasses import asdict, dataclass

from .attention import ThresholdAttention
from .models import Modality, SensoryEvent
from .runtime import SensumRuntime


@dataclass(slots=True, frozen=True)
class BenchmarkResult:
    raw_observations: int
    semantic_events: int
    emitted_to_reasoner: int
    attention_suppressed: int
    important_events: int
    important_emitted: int

    @property
    def total_reduction_ratio(self) -> float:
        if self.raw_observations == 0:
            return 0.0
        return 1.0 - (self.emitted_to_reasoner / self.raw_observations)

    @property
    def important_recall(self) -> float:
        if self.important_events == 0:
            return 1.0
        return self.important_emitted / self.important_events

    def to_dict(self) -> dict[str, int | float]:
        data = asdict(self)
        data["total_reduction_ratio"] = round(self.total_reduction_ratio, 6)
        data["important_recall"] = round(self.important_recall, 6)
        return data


async def run_synthetic_benchmark(
    *, observations: int = 10_000, seed: int = 7, sensor_pass_rate: float = 0.08
) -> BenchmarkResult:
    """Deterministic synthetic benchmark for the two-stage Sensum gating model.

    This does not claim real-world accuracy. It exists to make token/call reduction measurable
    from day one and to provide a stable regression target until public real-world datasets land.
    """

    if observations < 1:
        raise ValueError("observations must be >= 1")
    if not 0.0 < sensor_pass_rate <= 1.0:
        raise ValueError("sensor_pass_rate must be in (0, 1]")

    rng = random.Random(seed)
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=0.55))
    semantic_events = 0
    important_events = 0
    important_emitted = 0

    for _ in range(observations):
        if rng.random() > sensor_pass_rate:
            continue

        semantic_events += 1
        important = rng.random() < 0.08
        if important:
            important_events += 1
            event = SensoryEvent(
                kind="world.important_change",
                source="benchmark",
                modality=Modality.CUSTOM,
                summary="Synthetic important change",
                confidence=0.98,
                novelty=0.92,
                urgency=0.88,
                tags=["important", "interrupt"],
            )
        else:
            event = SensoryEvent(
                kind="world.minor_change",
                source="benchmark",
                modality=Modality.CUSTOM,
                summary="Synthetic low-value change",
                confidence=0.95,
                novelty=rng.uniform(0.02, 0.22),
                urgency=rng.uniform(0.0, 0.08),
                tags=["noise"],
            )

        emitted = await runtime.ingest(event)
        if important and emitted:
            important_emitted += 1

    return BenchmarkResult(
        raw_observations=observations,
        semantic_events=semantic_events,
        emitted_to_reasoner=runtime.stats.emitted,
        attention_suppressed=runtime.stats.suppressed,
        important_events=important_events,
        important_emitted=important_emitted,
    )
