"""Run Sensum's deterministic privacy-safe reference benchmark suite."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from generate_reference_fixtures import ROOT
from generate_reference_fixtures import main as generate_fixtures

from sensum.recorded_benchmark import load_jsonl, run_recorded_benchmark

TRACKS = ("browser", "audio", "screen", "vision")


async def _run(threshold: float) -> dict[str, object]:
    tracks: dict[str, dict[str, object]] = {}
    totals = {
        "cases": 0,
        "raw_observations": 0,
        "raw_bytes": 0,
        "semantic_events": 0,
        "reasoning_events": 0,
        "important_events": 0,
        "important_detected": 0,
        "false_positives": 0,
    }

    for name in TRACKS:
        result = await run_recorded_benchmark(
            load_jsonl(ROOT / f"{name}.jsonl"), threshold=threshold
        )
        payload = result.to_dict()
        tracks[name] = payload
        for key in totals:
            totals[key] += int(payload[key])

    important = totals["important_events"]
    detected = totals["important_detected"]
    positives = detected + totals["false_positives"]
    raw = totals["raw_observations"]
    reasoning = totals["reasoning_events"]
    summary = {
        **totals,
        "recall": round(1.0 if not important else detected / important, 6),
        "precision": round(1.0 if not positives else detected / positives, 6),
        "reasoning_reduction": round(0.0 if not raw else 1.0 - reasoning / raw, 6),
    }
    return {
        "suite": "sensum-reference-v1",
        "provenance": "generated_reference",
        "real_world": False,
        "threshold": threshold,
        "tracks": tracks,
        "summary": summary,
        "warning": "Reference/regression data only; do not present as real-world field performance.",
    }


def _check(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    assert isinstance(summary, dict)
    recall = float(summary["recall"])
    precision = float(summary["precision"])
    reduction = float(summary["reasoning_reduction"])
    if recall < 0.95:
        raise SystemExit(f"reference recall regression: {recall:.4f} < 0.95")
    if precision < 0.90:
        raise SystemExit(f"reference precision regression: {precision:.4f} < 0.90")
    if reduction < 0.95:
        raise SystemExit(f"reference reasoning reduction regression: {reduction:.4f} < 0.95")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sensum deterministic reference benchmarks")
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument(
        "--generate", action="store_true", help="Regenerate privacy-safe fixtures first"
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail on reference-regression thresholds"
    )
    parser.add_argument("--output", type=Path, help="Optional JSON result file")
    args = parser.parse_args()

    if args.generate or not all((ROOT / f"{name}.jsonl").exists() for name in TRACKS):
        generate_fixtures()

    payload = asyncio.run(_run(args.threshold))
    if args.check:
        _check(payload)

    encoded = json.dumps(payload, indent=2)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
