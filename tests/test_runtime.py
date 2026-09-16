import asyncio

import pytest

from sensum import Modality, SensoryEvent, SensumRuntime, ThresholdAttention


@pytest.mark.asyncio
async def test_runtime_suppresses_noise_and_emits_signal() -> None:
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=0.55))

    noise = SensoryEvent(kind="screen.minor_change", source="screen", modality=Modality.SCREEN, summary="Tiny change", novelty=0.05, urgency=0.0, confidence=1.0)
    signal = SensoryEvent(kind="user.interrupted", source="audio", modality=Modality.AUDIO, summary="User interrupted the agent", novelty=0.9, urgency=0.8, confidence=0.95, tags=["interrupt"])

    assert await runtime.ingest(noise) is False

    async def receive():
        return await anext(runtime.events())

    task = asyncio.create_task(receive())
    await asyncio.sleep(0)
    assert await runtime.ingest(signal) is True
    received = await asyncio.wait_for(task, timeout=1)

    assert received.id == signal.id
    assert runtime.stats.observed == 2
    assert runtime.stats.suppressed == 1
    assert runtime.stats.emitted == 1
