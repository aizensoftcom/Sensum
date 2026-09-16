from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from sensum.models import Modality, SensoryEvent, StateChange


class ScreenSensor:
    """Optional low-cost screen-change detector that never sends frames to an LLM."""

    def __init__(self, *, interval: float = 0.6, threshold: float = 0.035, monitor: int = 1, name: str = "screen") -> None:
        self.interval = interval
        self.threshold = threshold
        self.monitor = monitor
        self.name = name
        self._previous: Any = None

    async def events(self) -> AsyncIterator[SensoryEvent]:
        try:
            import mss  # type: ignore
            from PIL import Image, ImageChops, ImageStat  # type: ignore
        except ImportError as exc:
            raise RuntimeError("ScreenSensor requires optional dependencies: pip install 'sensum-ai[screen]'") from exc

        with mss.mss() as capture:
            if self.monitor >= len(capture.monitors):
                raise ValueError(f"monitor {self.monitor} does not exist")
            monitor = capture.monitors[self.monitor]
            while True:
                raw = capture.grab(monitor)
                image = Image.frombytes("RGB", raw.size, raw.rgb).resize((160, 90))
                if self._previous is not None:
                    diff = ImageChops.difference(self._previous, image)
                    stat = ImageStat.Stat(diff)
                    ratio = sum(stat.mean) / (3 * 255)
                    if ratio >= self.threshold:
                        yield SensoryEvent(kind="screen.changed", source=self.name, modality=Modality.SCREEN, entity=f"screen:{self.monitor}", summary=f"Screen changed ({ratio:.1%} mean pixel delta)", changes=[StateChange("change_ratio", None, round(ratio, 5))], confidence=1.0, novelty=min(1.0, 0.45 + ratio * 4), urgency=0.05, metadata={"monitor": self.monitor, "change_ratio": ratio}, tags=["changed"])
                self._previous = image
                await asyncio.sleep(self.interval)
