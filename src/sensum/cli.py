from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .attention import ThresholdAttention
from .benchmark import run_synthetic_benchmark
from .capture import (
    capture_audio_fixture,
    capture_browser_fixture,
    capture_screen_fixture,
    label_raw_fixture,
)
from .fusion import DEFAULT_RULES, TemporalFusionEngine
from .persistence import SQLiteEventStore
from .raw_benchmark import load_raw_jsonl, run_raw_benchmark
from .recorded_benchmark import load_jsonl, run_recorded_benchmark
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


async def _benchmark_recorded(path: Path, threshold: float) -> None:
    result = await run_recorded_benchmark(load_jsonl(path), threshold=threshold)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


async def _benchmark_raw(path: Path, threshold: float) -> None:
    result = await run_raw_benchmark(load_raw_jsonl(path), threshold=threshold)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def _serve(
    host: str,
    port: int,
    threshold: float,
    database: Path | None,
    enable_fusion: bool,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Sensum server dependencies are not installed. "
            "Install with: pip install -e '.[server]'"
        ) from exc

    from .gateway import create_app

    store = SQLiteEventStore(database) if database is not None else None
    fusion = TemporalFusionEngine(list(DEFAULT_RULES)) if enable_fusion else None
    runtime = SensumRuntime(
        attention=ThresholdAttention(threshold=threshold),
        store=store,
        fusion=fusion,
    )
    uvicorn.run(create_app(runtime), host=host, port=port)


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

    benchmark = sub.add_parser("benchmark", help="Run the synthetic regression benchmark")
    benchmark.add_argument("--observations", type=int, default=10_000)
    benchmark.add_argument("--seed", type=int, default=7)

    recorded = sub.add_parser(
        "benchmark-recorded",
        help="Run an event-level labelled JSONL benchmark fixture",
    )
    recorded.add_argument("fixture", type=Path)
    recorded.add_argument("--attention-threshold", type=float, default=0.55)

    raw = sub.add_parser(
        "benchmark-raw",
        help="Run a raw browser/audio/screen JSONL benchmark fixture",
    )
    raw.add_argument("fixture", type=Path)
    raw.add_argument("--attention-threshold", type=float, default=0.55)

    browser_capture = sub.add_parser(
        "capture-browser",
        help="Capture browser snapshots locally into an unlabelled raw fixture",
    )
    browser_capture.add_argument("url")
    browser_capture.add_argument("output", type=Path)
    browser_capture.add_argument("--seconds", type=float, default=30.0)
    browser_capture.add_argument("--interval", type=float, default=0.5)
    browser_capture.add_argument("--headless", action="store_true")

    screen_capture = sub.add_parser(
        "capture-screen",
        help="Capture screen deltas locally without storing screenshots",
    )
    screen_capture.add_argument("output", type=Path)
    screen_capture.add_argument("--seconds", type=float, default=30.0)
    screen_capture.add_argument("--interval", type=float, default=0.6)
    screen_capture.add_argument("--monitor", type=int, default=1)

    audio_capture = sub.add_parser(
        "capture-audio",
        help="Capture microphone PCM locally into an unlabelled raw fixture",
    )
    audio_capture.add_argument("output", type=Path)
    audio_capture.add_argument("--seconds", type=float, default=30.0)
    audio_capture.add_argument("--sample-rate", type=int, default=16_000)
    audio_capture.add_argument("--frame-ms", type=int, default=20)

    label = sub.add_parser(
        "label-raw",
        help="Interactively label expected and important events in a captured fixture",
    )
    label.add_argument("source", type=Path)
    label.add_argument("output", type=Path)

    serve = sub.add_parser("serve", help="Run the local Sensum live gateway and dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--attention-threshold", type=float, default=0.55)
    serve.add_argument("--db", type=Path, help="Persist semantic events to SQLite")
    serve.add_argument("--fusion", action="store_true", help="Enable default fusion rules")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "watch-files":
        asyncio.run(_watch_files(args.path, args.attention_threshold))
    elif args.command == "watch-screen":
        asyncio.run(_watch_screen(args.attention_threshold, args.pixel_threshold))
    elif args.command == "benchmark":
        asyncio.run(_benchmark(args.observations, args.seed))
    elif args.command == "benchmark-recorded":
        asyncio.run(_benchmark_recorded(args.fixture, args.attention_threshold))
    elif args.command == "benchmark-raw":
        asyncio.run(_benchmark_raw(args.fixture, args.attention_threshold))
    elif args.command == "capture-browser":
        count = asyncio.run(
            capture_browser_fixture(
                args.url,
                args.output,
                seconds=args.seconds,
                interval=args.interval,
                headless=args.headless,
            )
        )
        print(f"captured {count} browser observations -> {args.output}")
    elif args.command == "capture-screen":
        count = capture_screen_fixture(
            args.output,
            seconds=args.seconds,
            interval=args.interval,
            monitor=args.monitor,
        )
        print(f"captured {count} screen observations -> {args.output}")
    elif args.command == "capture-audio":
        count = capture_audio_fixture(
            args.output,
            seconds=args.seconds,
            sample_rate=args.sample_rate,
            frame_ms=args.frame_ms,
        )
        print(f"captured {count} audio observations -> {args.output}")
    elif args.command == "label-raw":
        count = label_raw_fixture(args.source, args.output)
        print(f"labelled {count} observations -> {args.output}")
    elif args.command == "serve":
        _serve(args.host, args.port, args.attention_threshold, args.db, args.fusion)


if __name__ == "__main__":
    main()
