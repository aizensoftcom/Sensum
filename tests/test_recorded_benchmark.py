import pytest

from sensum.models import Modality, SensoryEvent
from sensum.recorded_benchmark import RecordedCase, run_recorded_benchmark


@pytest.mark.asyncio
async def test_recorded_benchmark_reports_recall_precision_and_reduction() -> None:
    cases = [
        RecordedCase(
            SensoryEvent(
                kind="user.interrupted_agent",
                source="audio",
                modality=Modality.AUDIO,
                summary="Interrupted",
                confidence=0.99,
                novelty=0.95,
                urgency=0.95,
                tags=["interrupt", "important"],
            ),
            important=True,
            raw_observations=100,
            raw_bytes=32000,
        ),
        RecordedCase(
            SensoryEvent(
                kind="screen.minor_change",
                source="screen",
                modality=Modality.SCREEN,
                summary="Minor",
                confidence=0.9,
                novelty=0.05,
                urgency=0.01,
            ),
            important=False,
            raw_observations=100,
            raw_bytes=32000,
        ),
    ]

    result = await run_recorded_benchmark(cases)

    assert result.recall == 1.0
    assert result.precision == 1.0
    assert result.reasoning_events == 1
    assert result.reasoning_reduction > 0.99
