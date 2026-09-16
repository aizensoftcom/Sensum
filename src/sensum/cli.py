from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .attention import ThresholdAttention
from .benchmark import run_synthetic_benchmark
from .runtime import SensumRuntime
from .sensors import FileSensor, ScreenSensor


async def _print_events(runtime: SensumRuntime) -> None:
    async for event in runtime.events():
        print(json.dumps(event.to_dict(), ensure_ascii=False))


async def _watch_files(path: Path, threshold: float) -> None:
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=threshold))
    runtime.add_sensor(FileSensor(path))
    await runtime.start()
    try:
        await _print_events(runtime)
    finally:
        await runtime.stop()


async def _watch_screen(threshold: float, pixel_threshold: float) -> None:
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=threshold))
    runtime.add_sensor(ScreenSensor(threshold=pixel_threshold))
    await runtime.start()
    try:
        await _print_events(runtime)
    finally:
        await runtime.stop()


async def _benchmark(observations: int, seed: int) -> None:
    result = await run_synthetic_benchmark(observations=observations, seed=seed)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sensum",
        description="Continuous perception without continuous LLM inference.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    files = sub.add_parser("watch-files", help="Emit meaningful file-system deltas")
    files.add_argument("path", type=Path)
    files.add_argument("--attention-threshold", type=float, default=0.55)

    screen = sub.add_parser("watch-screen", help="Emit screen change events (optional deps)")
    screen.add_argument("--attention-threshold", type=float, default=0.55)
    screen.add_argument("--pixel-threshold", type=float, default=0.035)

    benchmark = sub.add_parser(
        "benchmark", help="Run the deterministic v0.2 two-stage filtering benchmark"
    )
    benchmark.add_argument("--observations", type=int, default=10_000)
    benchmark.add_argument("--seed", type=int, default=7)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "watch-files":
        asyncio.run(_watch_files(args.path, args.attention_threshold))
    elif args.command == "watch-screen":
        asyncio.run(_watch_screen(args.attention_threshold, args.pixel_threshold))
    elif args.command == "benchmark":
        asyncio.run(_benchmark(args.observations, args.seed))


if __name__ == "__main__":
    main()
