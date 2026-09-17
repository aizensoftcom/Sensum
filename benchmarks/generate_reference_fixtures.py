"""Generate deterministic, privacy-safe Sensum reference benchmark fixtures.

These fixtures are not field recordings and must never be presented as real-world performance
measurements. They exist to make the benchmark harness reproducible and to exercise browser,
audio, screen, and vision-style event tracks without committing private/customer media.
"""

from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent / "fixtures" / "reference"
SAMPLE_RATE = 16_000


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _event(
    kind: str,
    *,
    source: str,
    modality: str,
    summary: str,
    important: bool,
    raw_observations: int,
    raw_bytes: int,
    confidence: float,
    novelty: float,
    urgency: float,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "important": important,
        "raw_observations": raw_observations,
        "raw_bytes": raw_bytes,
        "event": {
            "kind": kind,
            "source": source,
            "modality": modality,
            "summary": summary,
            "confidence": confidence,
            "novelty": novelty,
            "urgency": urgency,
            "tags": tags or [],
        },
    }


def browser_rows() -> list[dict[str, Any]]:
    return [
        _event("browser.heartbeat", source="browser-ref", modality="browser", summary="No material DOM change", important=False, raw_observations=180, raw_bytes=1_800_000, confidence=0.99, novelty=0.01, urgency=0.0),
        _event("browser.navigated", source="browser-ref", modality="browser", summary="User navigated to checkout", important=True, raw_observations=30, raw_bytes=320_000, confidence=0.99, novelty=0.90, urgency=0.45, tags=["navigation"]),
        _event("browser.modal_opened", source="browser-ref", modality="browser", summary="Cookie modal opened", important=False, raw_observations=20, raw_bytes=210_000, confidence=0.98, novelty=0.35, urgency=0.05),
        _event("browser.price_changed", source="browser-ref", modality="browser", summary="Displayed price changed", important=True, raw_observations=60, raw_bytes=640_000, confidence=0.97, novelty=0.92, urgency=0.55, tags=["price", "important"]),
        _event("browser.modal_closed", source="browser-ref", modality="browser", summary="Cookie modal closed", important=False, raw_observations=20, raw_bytes=210_000, confidence=0.98, novelty=0.30, urgency=0.05),
        _event("payment.status_changed", source="browser-ref", modality="browser", summary="Payment status changed to completed", important=True, raw_observations=120, raw_bytes=1_200_000, confidence=0.995, novelty=0.99, urgency=0.85, tags=["payment", "important"]),
        _event("browser.heartbeat", source="browser-ref", modality="browser", summary="No material DOM change", important=False, raw_observations=240, raw_bytes=2_400_000, confidence=0.99, novelty=0.01, urgency=0.0),
    ]


def audio_rows(wav_bytes: int) -> list[dict[str, Any]]:
    return [
        _event("audio.silence", source="audio-ref", modality="audio", summary="Silence window", important=False, raw_observations=100, raw_bytes=wav_bytes // 5, confidence=1.0, novelty=0.0, urgency=0.0),
        _event("speech.started", source="audio-ref", modality="audio", summary="Speech started", important=True, raw_observations=35, raw_bytes=wav_bytes // 8, confidence=0.96, novelty=0.82, urgency=0.45, tags=["speech"]),
        _event("speech.continued", source="audio-ref", modality="audio", summary="Speech continued", important=False, raw_observations=80, raw_bytes=wav_bytes // 4, confidence=0.95, novelty=0.10, urgency=0.05),
        _event("user.interrupted_agent", source="audio-ref", modality="audio", summary="User interrupted agent playback", important=True, raw_observations=25, raw_bytes=wav_bytes // 10, confidence=0.98, novelty=0.98, urgency=0.98, tags=["interrupt", "important"]),
        _event("speech.ended", source="audio-ref", modality="audio", summary="Speech ended", important=True, raw_observations=35, raw_bytes=wav_bytes // 8, confidence=0.97, novelty=0.78, urgency=0.30, tags=["speech"]),
        _event("audio.silence", source="audio-ref", modality="audio", summary="Silence window", important=False, raw_observations=120, raw_bytes=wav_bytes // 5, confidence=1.0, novelty=0.0, urgency=0.0),
    ]


def screen_rows() -> list[dict[str, Any]]:
    return [
        _event("screen.churn", source="screen-ref", modality="screen", summary="Caret and clock churn", important=False, raw_observations=300, raw_bytes=9_000_000, confidence=0.99, novelty=0.02, urgency=0.0),
        _event("screen.changed", source="screen-ref", modality="screen", summary="New application view appeared", important=True, raw_observations=45, raw_bytes=1_350_000, confidence=0.96, novelty=0.85, urgency=0.35),
        _event("screen.toast", source="screen-ref", modality="screen", summary="Low-value transient toast", important=False, raw_observations=25, raw_bytes=750_000, confidence=0.94, novelty=0.30, urgency=0.05),
        _event("screen.error_dialog", source="screen-ref", modality="screen", summary="Blocking error dialog appeared", important=True, raw_observations=60, raw_bytes=1_800_000, confidence=0.98, novelty=0.96, urgency=0.92, tags=["error", "important"]),
        _event("screen.churn", source="screen-ref", modality="screen", summary="Animation churn", important=False, raw_observations=220, raw_bytes=6_600_000, confidence=0.99, novelty=0.03, urgency=0.0),
    ]


def vision_rows() -> list[dict[str, Any]]:
    return [
        _event("vision.motion", source="vision-ref", modality="vision", summary="Background motion", important=False, raw_observations=150, raw_bytes=18_000_000, confidence=0.92, novelty=0.12, urgency=0.02),
        _event("person.entered", source="vision-ref", modality="vision", summary="Person entered monitored area", important=True, raw_observations=30, raw_bytes=3_600_000, confidence=0.95, novelty=0.91, urgency=0.55, tags=["person", "important"]),
        _event("package.left", source="vision-ref", modality="vision", summary="Package left on table", important=True, raw_observations=45, raw_bytes=5_400_000, confidence=0.93, novelty=0.95, urgency=0.60, tags=["object", "important"]),
        _event("vision.motion", source="vision-ref", modality="vision", summary="Background motion", important=False, raw_observations=180, raw_bytes=21_600_000, confidence=0.91, novelty=0.10, urgency=0.02),
    ]


def write_audio_fixture(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    segments = [
        (1.0, 0.0),
        (0.8, 330.0),
        (0.5, 0.0),
        (0.9, 440.0),
        (0.6, 0.0),
    ]
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        for duration, frequency in segments:
            frames = int(duration * SAMPLE_RATE)
            for index in range(frames):
                sample = 0 if frequency == 0 else int(9_000 * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
                wav.writeframesraw(struct.pack("<h", sample))
    return path.stat().st_size


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    wav_path = ROOT / "audio-reference.wav"
    wav_bytes = write_audio_fixture(wav_path)
    _write_jsonl(ROOT / "browser.jsonl", browser_rows())
    _write_jsonl(ROOT / "audio.jsonl", audio_rows(wav_bytes))
    _write_jsonl(ROOT / "screen.jsonl", screen_rows())
    _write_jsonl(ROOT / "vision.jsonl", vision_rows())

    manifest = {
        "name": "Sensum deterministic reference suite",
        "provenance": "generated_reference",
        "real_world": False,
        "privacy": "contains no customer, personal, microphone, camera, or browsing data",
        "audio": {
            "file": "audio-reference.wav",
            "sample_rate_hz": SAMPLE_RATE,
            "content": "synthetic sine tones and silence; not human speech",
        },
        "tracks": ["browser", "audio", "screen", "vision"],
        "warning": "Do not publish these results as real-world field measurements.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(ROOT)


if __name__ == "__main__":
    main()
