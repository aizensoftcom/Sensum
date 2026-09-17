import pytest

from sensum.benchmark import run_synthetic_benchmark


@pytest.mark.asyncio
async def test_benchmark_preserves_important_events_and_reduces_calls() -> None:
    result = await run_synthetic_benchmark(observations=5_000, seed=7)

    assert result.important_events > 0
    assert result.important_recall == 1.0
    assert result.total_reduction_ratio > 0.98
    assert result.emitted_to_reasoner < result.semantic_events < result.raw_observations
