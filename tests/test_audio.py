from __future__ import annotations

from array import array

import pytest

from sensum.sensors import AudioFrame, AudioVADSensor, EnergyVAD


def _pcm(amplitude: int, samples: int = 160) -> bytes:
    return array("h", [amplitude] * samples).tobytes()


class _Source:
    def __init__(self, frames: list[AudioFrame]) -> None:
        self.frames = frames

    async def __aiter__(self):
        for frame in self.frames:
            yield frame


@pytest.mark.asyncio
async def test_audio_vad_emits_start_and_stop() -> None:
    frames = [
        AudioFrame(_pcm(0)),
        AudioFrame(_pcm(0)),
        AudioFrame(_pcm(4000)),
        AudioFrame(_pcm(4000)),
        AudioFrame(_pcm(0)),
        AudioFrame(_pcm(0)),
    ]
    sensor = AudioVADSensor(
        _Source(frames),
        vad=EnergyVAD(threshold=0.05),
        speech_frames=2,
        silence_frames=2,
    )

    events = [event async for event in sensor.events()]

    assert [event.kind for event in events] == ["speech.started", "speech.stopped"]
    assert sensor.stats.raw_observations == 6
    assert sensor.stats.semantic_events == 2
