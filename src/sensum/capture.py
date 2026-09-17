from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Any


def _append_row(handle: Any, payload: dict[str, Any]) -> None:
    handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    handle.flush()


async def capture_browser_fixture(
    url: str,
    output: str | Path,
    *,
    seconds: float = 30.0,
    interval: float = 0.5,
    headless: bool = False,
) -> int:
    """Capture browser snapshots locally into an unlabelled raw benchmark fixture."""

    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Browser capture requires: pip install 'sensum-ai[capture-browser]' "
            "and then: playwright install chromium"
        ) from exc

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(url)
        deadline = time.monotonic() + seconds
        handle = await asyncio.to_thread(path.open, "w", encoding="utf-8")
        try:
            while time.monotonic() < deadline:
                title = await page.title()
                text = await page.locator("body").inner_text()
                current_url = str(page.url)
                raw_bytes = len((current_url + title + text).encode("utf-8"))
                payload = {
                    "track": "browser",
                    "origin": "captured",
                    "raw_bytes": raw_bytes,
                    "observation": {
                        "url": current_url,
                        "title": title,
                        "text": text,
                    },
                }
                await asyncio.to_thread(_append_row, handle, payload)
                count += 1
                await asyncio.sleep(interval)
        finally:
            await asyncio.to_thread(handle.close)
            await browser.close()
    return count


def capture_screen_fixture(
    output: str | Path,
    *,
    seconds: float = 30.0,
    interval: float = 0.6,
    monitor: int = 1,
) -> int:
    """Capture local screen-change ratios without storing screenshots."""

    try:
        import mss
        from PIL import Image, ImageChops, ImageStat
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Screen capture requires: pip install 'sensum-ai[screen]'"
        ) from exc

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: Any = None
    count = 0
    deadline = time.monotonic() + seconds
    with mss.mss() as capture, path.open("w", encoding="utf-8") as handle:
        if monitor >= len(capture.monitors):
            raise ValueError(f"monitor {monitor} does not exist")
        monitor_spec = capture.monitors[monitor]
        while time.monotonic() < deadline:
            raw = capture.grab(monitor_spec)
            image = Image.frombytes("RGB", raw.size, raw.rgb).resize((160, 90))
            ratio = 0.0
            if previous is not None:
                diff = ImageChops.difference(previous, image)
                ratio = sum(ImageStat.Stat(diff).mean) / (3 * 255)
            _append_row(
                handle,
                {
                    "track": "screen",
                    "origin": "captured",
                    "raw_bytes": len(raw.rgb),
                    "observation": {
                        "change_ratio": round(ratio, 8),
                        "monitor": monitor,
                    },
                },
            )
            previous = image
            count += 1
            time.sleep(interval)
    return count


def capture_audio_fixture(
    output: str | Path,
    *,
    seconds: float = 30.0,
    sample_rate: int = 16_000,
    frame_ms: int = 20,
) -> int:
    """Capture microphone PCM frames locally into an unlabelled raw fixture."""

    try:
        import sounddevice as sd
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Audio capture requires: pip install 'sensum-ai[capture-audio]'"
        ) from exc

    blocksize = max(1, int(sample_rate * frame_ms / 1000))
    chunks: list[bytes] = []

    def callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
        del frames, time_info, status
        chunks.append(bytes(indata))

    deadline = time.monotonic() + seconds
    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=blocksize,
        channels=1,
        dtype="int16",
        callback=callback,
    ):
        while time.monotonic() < deadline:
            time.sleep(0.05)

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            _append_row(
                handle,
                {
                    "track": "audio",
                    "origin": "captured",
                    "raw_bytes": len(chunk),
                    "observation": {
                        "pcm16_b64": base64.b64encode(chunk).decode("ascii"),
                        "sample_rate": sample_rate,
                        "channels": 1,
                        "agent_speaking": False,
                    },
                },
            )
    return len(chunks)


def label_raw_fixture(source: str | Path, output: str | Path) -> int:
    """Interactively add expected/important event labels to a captured JSONL fixture."""

    source_path = Path(source)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source_path.open("r", encoding="utf-8") as source_handle, output_path.open(
        "w", encoding="utf-8"
    ) as output_handle:
        for line_number, line in enumerate(source_handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            payload = json.loads(line)
            print(f"\n[{line_number}] {payload['track']} {payload['observation']}")
            expected_text = input("Expected event kinds (comma-separated, blank = none): ").strip()
            important_text = input("Important subset (comma-separated, blank = none): ").strip()
            payload["expected"] = [
                item.strip() for item in expected_text.split(",") if item.strip()
            ]
            payload["important"] = [
                item.strip() for item in important_text.split(",") if item.strip()
            ]
            _append_row(output_handle, payload)
            count += 1
    return count
