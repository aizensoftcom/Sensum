from __future__ import annotations

import asyncio
import math
import sys
from array import array
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from sensum.models import Modality, SensoryEvent, StateChange

from .base import SensorStats


@dataclass(slots=True, frozen=True)
class AudioFrame:
    """A small signed-16-bit PCM audio frame.

    Sensum deliberately accepts frames from any source: microphone libraries, SIP stacks,
    WebRTC, files, or custom hardware.
    """

    pcm16: bytes
    sample_rate: int = 16_000
    channels: int = 1


class AudioFrameSource(Protocol):
    def __aiter__(self) -> AsyncIterator[AudioFrame]: ...


@dataclass(slots=True)
class EnergyVAD:
    """Tiny zero-model voice activity detector based on normalized RMS energy.

    This is the portable baseline gate. Applications can replace it with Silero, WebRTC VAD,
    or another local model while keeping the same sensor contract.
    """

    threshold: float = 0.025

    def score(self, frame: AudioFrame) -> float:
        if not frame.pcm16:
            return 0.0
        samples = array("h")
        samples.frombytes(frame.pcm16)
        if sys.byteorder != "little":
            samples.byteswap()
        if not samples:
            return 0.0
        mean_square = sum(float(sample) * float(sample) for sample in samples) / len(samples)
        return min(1.0, math.sqrt(mean_square) / 32768.0)

    def is_speech(self, frame: AudioFrame) -> bool:
        return self.score(frame) >= self.threshold


class AudioVADSensor:
    """Turns a continuous PCM stream into speech.started / speech.stopped events."""

    def __init__(
        self,
        source: AudioFrameSource,
        *,
        vad: EnergyVAD | None = None,
        speech_frames: int = 2,
        silence_frames: int = 4,
        name: str = "audio",
    ) -> None:
        if speech_frames < 1 or silence_frames < 1:
            raise ValueError("speech_frames and silence_frames must be >= 1")
        self.source = source
        self.vad = vad or EnergyVAD()
        self.speech_frames = speech_frames
        self.silence_frames = silence_frames
        self.name = name
        self.stats = SensorStats()

    async def events(self) -> AsyncIterator[SensoryEvent]:
        speaking = False
        voiced_run = 0
        silent_run = 0

        async for frame in self.source:
            self.stats.raw_observations += 1
            score = self.vad.score(frame)
            voiced = score >= self.vad.threshold

            if voiced:
                voiced_run += 1
                silent_run = 0
            else:
                silent_run += 1
                voiced_run = 0

            if not speaking and voiced_run >= self.speech_frames:
                speaking = True
                self.stats.semantic_events += 1
                yield SensoryEvent(
                    kind="speech.started",
                    source=self.name,
                    modality=Modality.AUDIO,
                    entity="audio:speaker",
                    summary="Speech started",
                    changes=[StateChange("speaking", False, True)],
                    confidence=min(1.0, 0.6 + score * 6),
                    novelty=0.82,
                    urgency=0.35,
                    metadata={"energy": round(score, 6), "sample_rate": frame.sample_rate},
                    tags=["speech", "started"],
                )
            elif speaking and silent_run >= self.silence_frames:
                speaking = False
                self.stats.semantic_events += 1
                yield SensoryEvent(
                    kind="speech.stopped",
                    source=self.name,
                    modality=Modality.AUDIO,
                    entity="audio:speaker",
                    summary="Speech stopped",
                    changes=[StateChange("speaking", True, False)],
                    confidence=0.95,
                    novelty=0.72,
                    urgency=0.15,
                    metadata={"silence_frames": silent_run, "sample_rate": frame.sample_rate},
                    tags=["speech", "stopped"],
                )

            await asyncio.sleep(0)
