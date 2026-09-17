# ruff: noqa: I001

from pathlib import Path

import pytest

from sensum.raw_benchmark import load_raw_jsonl, run_raw_benchmark


FIXTURES = Path("benchmarks/fixtures")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,expected_events",
    [
        ("generated_browser.jsonl", 2),
        ("generated_audio.jsonl", 3),
        ("generated_screen.jsonl", 2),
    ],
)
async def test_generated_raw_fixtures_have_perfect_sensor_regression(
    name: str, expected_events: int
) -> None:
    result = await run_raw_benchmark(load_raw_jsonl(FIXTURES / name))

    assert result.evidence_class == "generated"
    assert result.expected_events == expected_events
    assert result.semantic_events == expected_events
    assert result.sensor_recall == 1.0
    assert result.sensor_precision == 1.0
    assert result.false_negatives == 0
    assert result.false_positives == 0


@pytest.mark.asyncio
async def test_audio_fixture_preserves_important_interruption() -> None:
    result = await run_raw_benchmark(load_raw_jsonl(FIXTURES / "generated_audio.jsonl"))

    assert result.important_events == 1
    assert result.important_reasoned == 1
    assert result.important_recall == 1.0
    assert 0.0 < result.reasoning_reduction < 1.0
