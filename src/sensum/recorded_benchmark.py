from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .attention import ThresholdAttention
from .models import Modality, SensoryEvent, StateChange
from .runtime import SensumRuntime


@dataclass(slots=True, frozen=True)
class RecordedCase:
    event: SensoryEvent
    important: bool
    raw_observations: int = 1
    raw_bytes: int = 0


@dataclass(slots=True, frozen=True)
class RecordedBenchmarkResult:
    cases: int
    raw_observations: int
    raw_bytes: int
    semantic_events: int
    reasoning_events: int
    important_events: int
    important_detected: int
    false_positives: int
    elapsed_ms: float

    @property
    def recall(self) -> float:
        return 1.0 if not self.important_events else self.important_detected / self.important_events

    @property
    def precision(self) -> float:
        denominator = self.important_detected + self.false_positives
        return 1.0 if denominator == 0 else self.important_detected / denominator

    @property
    def reasoning_reduction(self) -> float:
        if not self.raw_observations:
            return 0.0
        return 1.0 - self.reasoning_events / self.raw_observations

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.update(
            recall=round(self.recall, 6),
            precision=round(self.precision, 6),
            reasoning_reduction=round(self.reasoning_reduction, 6),
        )
        return result


def load_jsonl(path: str | Path) -> list[RecordedCase]:
    cases: list[RecordedCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}") from exc
            event_data = payload["event"]
            event = SensoryEvent(
                kind=str(event_data["kind"]),
                source=str(event_data.get("source", "recorded")),
                modality=Modality(str(event_data.get("modality", "custom"))),
                summary=str(event_data.get("summary", event_data["kind"])),
                entity=event_data.get("entity"),
                changes=[
                    StateChange(str(change["path"]), change.get("before"), change.get("after"))
                    for change in event_data.get("changes", [])
                ],
                confidence=float(event_data.get("confidence", 1.0)),
                novelty=float(event_data.get("novelty", 0.5)),
                urgency=float(event_data.get("urgency", 0.0)),
                metadata=dict(event_data.get("metadata", {})),
                tags=list(event_data.get("tags", [])),
            )
            cases.append(
                RecordedCase(
                    event=event,
                    important=bool(payload.get("important", False)),
                    raw_observations=int(payload.get("raw_observations", 1)),
                    raw_bytes=int(payload.get("raw_bytes", 0)),
                )
            )
    return cases


async def run_recorded_benchmark(
    cases: list[RecordedCase], *, threshold: float = 0.55
) -> RecordedBenchmarkResult:
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=threshold))
    important_events = 0
    important_detected = 0
    false_positives = 0
    started = time.perf_counter()

    for case in cases:
        if case.important:
            important_events += 1
        emitted = await runtime.ingest(case.event)
        if emitted and case.important:
            important_detected += 1
        elif emitted and not case.important:
            false_positives += 1

    elapsed_ms = (time.perf_counter() - started) * 1000
    return RecordedBenchmarkResult(
        cases=len(cases),
        raw_observations=sum(case.raw_observations for case in cases),
        raw_bytes=sum(case.raw_bytes for case in cases),
        semantic_events=len(cases),
        reasoning_events=runtime.stats.emitted,
        important_events=important_events,
        important_detected=important_detected,
        false_positives=false_positives,
        elapsed_ms=round(elapsed_ms, 3),
    )
