"""Run Sensum against a labelled recorded JSONL fixture.

This command never invents performance numbers. Supply captured observations converted into the
fixture format documented in docs/benchmarking.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json

from sensum.recorded_benchmark import load_jsonl, run_recorded_benchmark


async def _main(path: str, threshold: float) -> None:
    result = await run_recorded_benchmark(load_jsonl(path), threshold=threshold)
    print(json.dumps(result.to_dict(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a labelled recorded Sensum benchmark")
    parser.add_argument("fixture")
    parser.add_argument("--threshold", type=float, default=0.55)
    args = parser.parse_args()
    asyncio.run(_main(args.fixture, args.threshold))


if __name__ == "__main__":
    main()
