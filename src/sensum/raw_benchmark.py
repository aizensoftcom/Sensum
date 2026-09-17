from __future__ import annotations

import asyncio
import base64
import json
import struct
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .attention import ThresholdAttention
from .models import Modality, SensoryEvent, StateChange
from .runtime import SensumRuntime
from .sensors.audio import AgentSpeakingState, AudioFrame, AudioVADSensor
from .sensors.browser import BrowserSensor, BrowserSnapshot


@dataclass(slots=True, frozen=True)
class RawFixtureRow:
    track: str
    observation: dict[str, Any]
    expected: tuple[str, ...] = ()
    important: tuple[str, ...] = ()
    raw_bytes: int = 0
    origin: str = "unknown"
    labelled: bool = False


@dataclass(slots=True, frozen=True)
class RawBenchmarkResult:
    rows: int
    labelled_rows: int
    raw_observations: int
    raw_bytes: int
    expected_events: int
    semantic_events: int
    true_positives: int
    false_positives: int
    false_negatives: int
    reasoning_events: int
    important_events: int
    important_reasoned: int
    elapsed_ms: float
    origins: tuple[str, ...]

    @property
    def fully_labelled(self) -> bool:
        return self.rows > 0 and self.labelled_rows == self.rows

    @property
    def sensor_recall(self) -> float | None:
        if not self.fully_labelled:
            return None
        denominator = self.true_positives + self.false_negatives
        return 1.0 if denominator == 0 else self.true_positives / denominator

    @property
    def sensor_precision(self) -> float | None:
        if not self.fully_labelled:
            return None
        denominator = self.true_positives + self.false_positives
        return 1.0 if denominator == 0 else self.true_positives / denominator

    @property
    def reasoning_reduction(self) -> float:
        if self.raw_observations == 0:
            return 0.0
        return 1.0 - self.reasoning_events / self.raw_observations

    @property
    def important_recall(self) -> float | None:
        if not self.fully_labelled:
            return None
        if self.important_events == 0:
            return 1.0
        return self.important_reasoned / self.important_events

    @property
    def evidence_class(self) -> str:
        origins = set(self.origins)
        if origins == {"captured"}:
            return "captured"
        if origins == {"generated"}:
            return "generated"
        if "captured" in origins and "generated" in origins:
            return "mixed"
        return "unclassified"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.update(
            fully_labelled=self.fully_labelled,
            sensor_recall=(
                None if self.sensor_recall is None else round(self.sensor_recall, 6)
            ),
            sensor_precision=(
                None if self.sensor_precision is None else round(self.sensor_precision, 6)
            ),
            reasoning_reduction=round(self.reasoning_reduction, 6),
            important_recall=(
                None if self.important_recall is None else round(self.important_recall, 6)
            ),
            evidence_class=self.evidence_class,
        )
        return result


def load_raw_jsonl(path: str | Path) -> list[RawFixtureRow]:
    rows: list[RawFixtureRow] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}") from exc
            expected = payload.get("expected")
            important = payload.get("important")
            rows.append(
                RawFixtureRow(
                    track=str(payload["track"]),
                    observation=dict(payload["observation"]),
                    expected=tuple(str(item) for item in (expected or [])),
                    important=tuple(str(item) for item in (important or [])),
                    raw_bytes=int(payload.get("raw_bytes", 0)),
                    origin=str(payload.get("origin", "unknown")),
                    labelled="expected" in payload,
                )
            )
    return rows


def _pcm_frame(observation: dict[str, Any]) -> AudioFrame:
    sample_rate = int(observation.get("sample_rate", 16_000))
    channels = int(observation.get("channels", 1))
    if "pcm16_b64" in observation:
        pcm16 = base64.b64decode(str(observation["pcm16_b64"]), validate=True)
    else:
        amplitude = int(observation.get("amplitude", 0))
        samples = int(observation.get("samples", 320))
        amplitude = max(-32768, min(32767, amplitude))
        pcm16 = struct.pack(f"<{samples}h", *([amplitude] * samples))
    return AudioFrame(pcm16=pcm16, sample_rate=sample_rate, channels=channels)


async def _run_audio(rows: list[RawFixtureRow]) -> list[SensoryEvent]:
    state = AgentSpeakingState()

    class FixtureSource:
        async def __aiter__(self):
            for row in rows:
                state.speaking = bool(row.observation.get("agent_speaking", False))
                yield _pcm_frame(row.observation)
                await asyncio.sleep(0)

    sensor = AudioVADSensor(FixtureSource(), agent_speaking=state)
    return [event async for event in sensor.events()]


def _run_browser(rows: list[RawFixtureRow]) -> list[SensoryEvent]:
    events: list[SensoryEvent] = []
    previous: BrowserSnapshot | None = None
    sensor = BrowserSensor(lambda: None)  # type: ignore[arg-type]
    for row in rows:
        data = row.observation
        current = BrowserSnapshot(
            url=str(data.get("url", "about:blank")),
            title=str(data.get("title", "")),
            text=str(data.get("text", "")),
        )
        if previous is not None:
            event = sensor._compare(previous, current)
            if event is not None:
                events.append(event)
        previous = current
    return events


def _run_screen(rows: list[RawFixtureRow], *, threshold: float = 0.035) -> list[SensoryEvent]:
    events: list[SensoryEvent] = []
    for row in rows:
        ratio = float(row.observation.get("change_ratio", 0.0))
        if ratio < threshold:
            continue
        events.append(
            SensoryEvent(
                kind="screen.changed",
                source="screen-fixture",
                modality=Modality.SCREEN,
                entity="screen:1",
                summary=f"Screen changed ({ratio:.1%} mean pixel delta)",
                changes=[StateChange("change_ratio", None, round(ratio, 5))],
                confidence=1.0,
                novelty=min(1.0, 0.45 + ratio * 4),
                urgency=0.05,
                metadata={"monitor": 1, "change_ratio": ratio},
                tags=["changed"],
            )
        )
    return events


async def run_raw_benchmark(
    rows: list[RawFixtureRow], *, threshold: float = 0.55
) -> RawBenchmarkResult:
    started = time.perf_counter()
    tracks: dict[str, list[RawFixtureRow]] = {}
    for row in rows:
        tracks.setdefault(row.track, []).append(row)

    produced: list[SensoryEvent] = []
    if browser_rows := tracks.get("browser"):
        produced.extend(_run_browser(browser_rows))
    if audio_rows := tracks.get("audio"):
        produced.extend(await _run_audio(audio_rows))
    if screen_rows := tracks.get("screen"):
        produced.extend(_run_screen(screen_rows))

    unknown = sorted(set(tracks) - {"browser", "audio", "screen"})
    if unknown:
        raise ValueError(f"unsupported raw benchmark track(s): {', '.join(unknown)}")

    fully_labelled = bool(rows) and all(row.labelled for row in rows)
    expected = Counter(kind for row in rows for kind in row.expected)
    predicted = Counter(event.kind for event in produced)
    if fully_labelled:
        true_positives = sum((expected & predicted).values())
        false_positives = sum((predicted - expected).values())
        false_negatives = sum((expected - predicted).values())
    else:
        true_positives = false_positives = false_negatives = 0

    important = Counter(kind for row in rows for kind in row.important)
    important_remaining = important.copy()
    important_reasoned = 0
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=threshold))
    for event in produced:
        emitted = await runtime.ingest(event)
        if emitted and important_remaining[event.kind] > 0:
            important_reasoned += 1
            important_remaining[event.kind] -= 1

    elapsed_ms = (time.perf_counter() - started) * 1000
    origins = tuple(sorted({row.origin for row in rows}))
    return RawBenchmarkResult(
        rows=len(rows),
        labelled_rows=sum(1 for row in rows if row.labelled),
        raw_observations=len(rows),
        raw_bytes=sum(row.raw_bytes for row in rows),
        expected_events=sum(expected.values()),
        semantic_events=len(produced),
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        reasoning_events=runtime.stats.emitted,
        important_events=sum(important.values()),
        important_reasoned=important_reasoned,
        elapsed_ms=round(elapsed_ms, 3),
        origins=origins,
    )
