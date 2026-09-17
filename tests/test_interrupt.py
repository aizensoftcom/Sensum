from __future__ import annotations

from array import array

import pytest

from sensum.sensors import AgentSpeakingState, AudioFrame, AudioVADSensor, EnergyVAD


def _pcm(amplitude: int, samples: int = 160) -> bytes:
    return array("h", [amplitude] * samples).tobytes()


class _Source:
    def __init__(self, frames: list[AudioFrame]) -> None:
        self.frames = frames

    async def __aiter__(self):
        for frame in self.frames:
            yield frame


@pytest.mark.asyncio
async def test_audio_emits_interruption_when_agent_is_speaking() -> None:
    state = AgentSpeakingState(speaking=True)
    source = _Source([AudioFrame(_pcm(5000)), AudioFrame(_pcm(5000))])
    sensor = AudioVADSensor(
        source,
        vad=EnergyVAD(threshold=0.05),
        speech_frames=2,
        silence_frames=2,
        agent_speaking=state,
    )

    events = [event async for event in sensor.events()]

    assert [event.kind for event in events] == [
        "speech.started",
        "user.interrupted_agent",
    ]
    interruption = events[1]
    assert interruption.urgency == 0.95
    assert "interrupt" in interruption.tags
