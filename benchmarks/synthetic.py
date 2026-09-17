"""Reproducible synthetic benchmark for Sensum's attention boundary.

This benchmark is intentionally synthetic. It is a regression harness, not a product claim.
It asks one narrow question: if a continuous source produces many observations but only a
small fraction are meaningful, how many expensive reasoning calls can the attention layer avoid
while retaining events labelled important by the scenario?
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
from dataclasses import asdict, dataclass

from sensum import Modality, SensoryEvent, SensumRuntime
from sensum.attention import ThresholdAttention


@dataclass(slots=True)
class BenchmarkResult:
    raw_observations: int
    semantic_events: int
    reasoning_events: int
    important_events: int
    important_retained: int

    @property
    def reasoning_reduction(self) -> float:
        if not self.raw_observations:
            return 0.0
        return 1.0 - (self.reasoning_events / self.raw_observations)

    @property
    def important_recall(self) -> float:
        if not self.important_events:
            return 1.0
        return self.important_retained / self.important_events

    def to_dict(self) -> dict[str, int | float | str]:
        data = asdict(self)
        data["reasoning_reduction_pct"] = round(self.reasoning_reduction * 100, 4)
        data["important_recall_pct"] = round(self.important_recall * 100, 4)
        data["note"] = "Synthetic regression benchmark; not a real-world product measurement."
        return data


async def run(observations: int = 10_000, seed: int = 7) -> BenchmarkResult:
    rng = random.Random(seed)
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=0.55))
    semantic_events = 0
    important_events = 0
    important_retained = 0

    for index in range(observations):
        roll = rng.random()

        # Most continuous observations contain no semantic change and are removed by a local
        # detector before the runtime. About 8% become semantic events in this scenario.
        if roll >= 0.08:
            continue

        semantic_events += 1
        important = roll < 0.006
        if important:
            important_events += 1

        event = SensoryEvent(
            kind="benchmark.important_change" if important else "benchmark.minor_change",
            source="synthetic",
            modality=Modality.SENSOR,
            summary="Important synthetic change" if important else "Minor synthetic change",
            confidence=0.98,
            novelty=0.95 if important else 0.22,
            urgency=0.90 if important else 0.05,
            tags=["alarm"] if important else ["noise"],
            metadata={"observation": index, "important": important},
        )
        emitted = await runtime.ingest(event)
        if important and emitted:
            important_retained += 1

    return BenchmarkResult(
        raw_observations=observations,
        semantic_events=semantic_events,
        reasoning_events=runtime.stats.emitted,
        important_events=important_events,
        important_retained=important_retained,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Sensum synthetic regression benchmark")
    parser.add_argument("--observations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    result = asyncio.run(run(args.observations, args.seed))
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
