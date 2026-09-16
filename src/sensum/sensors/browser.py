from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from difflib import SequenceMatcher

from sensum.models import Modality, SensoryEvent, StateChange

from .base import SensorStats


@dataclass(slots=True, frozen=True)
class BrowserSnapshot:
    url: str
    title: str = ""
    text: str = ""

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8", errors="ignore")).hexdigest()[:16]


SnapshotProvider = Callable[[], Awaitable[BrowserSnapshot]]


class BrowserSensor:
    """Browser/DOM change sensor independent of any browser automation library.

    Pass an async snapshot provider from Playwright, Selenium, Electron, a browser extension,
    or any custom environment. Raw DOM/text snapshots remain local; only compact semantic
    deltas are emitted.
    """

    def __init__(
        self,
        provider: SnapshotProvider,
        *,
        interval: float = 0.5,
        text_change_threshold: float = 0.08,
        name: str = "browser",
    ) -> None:
        if not 0.0 <= text_change_threshold <= 1.0:
            raise ValueError("text_change_threshold must be between 0 and 1")
        self.provider = provider
        self.interval = interval
        self.text_change_threshold = text_change_threshold
        self.name = name
        self.stats = SensorStats()
        self._previous: BrowserSnapshot | None = None

    @classmethod
    def from_playwright_page(
        cls,
        page: object,
        *,
        interval: float = 0.5,
        text_change_threshold: float = 0.08,
        name: str = "browser",
    ) -> "BrowserSensor":
        async def provider() -> BrowserSnapshot:
            title = await page.title()  # type: ignore[attr-defined]
            text = await page.locator("body").inner_text()  # type: ignore[attr-defined]
            return BrowserSnapshot(url=str(page.url), title=title, text=text)  # type: ignore[attr-defined]

        return cls(
            provider,
            interval=interval,
            text_change_threshold=text_change_threshold,
            name=name,
        )

    async def events(self) -> AsyncIterator[SensoryEvent]:
        while True:
            current = await self.provider()
            self.stats.raw_observations += 1

            if self._previous is not None:
                event = self._compare(self._previous, current)
                if event is not None:
                    self.stats.semantic_events += 1
                    yield event

            self._previous = current
            await asyncio.sleep(self.interval)

    def _compare(self, before: BrowserSnapshot, after: BrowserSnapshot) -> SensoryEvent | None:
        changes: list[StateChange] = []
        tags: list[str] = []
        novelty = 0.0
        urgency = 0.05
        kind = "browser.changed"

        if before.url != after.url:
            kind = "browser.navigated"
            tags.append("navigation")
            changes.append(StateChange("url", before.url, after.url))
            novelty = max(novelty, 0.95)
            urgency = max(urgency, 0.15)

        if before.title != after.title:
            tags.append("title")
            changes.append(StateChange("title", before.title, after.title))
            novelty = max(novelty, 0.65)

        text_delta = 0.0
        if before.content_hash != after.content_hash:
            ratio = SequenceMatcher(None, before.text[:20_000], after.text[:20_000]).ratio()
            text_delta = 1.0 - ratio
            if text_delta >= self.text_change_threshold:
                tags.append("content")
                changes.extend(
                    [
                        StateChange("content_hash", before.content_hash, after.content_hash),
                        StateChange("text_length", len(before.text), len(after.text)),
                    ]
                )
                novelty = max(novelty, min(0.9, 0.35 + text_delta))

        if not changes:
            return None

        return SensoryEvent(
            kind=kind,
            source=self.name,
            modality=Modality.BROWSER,
            entity="browser:active-page",
            summary=self._summary(before, after, tags),
            changes=changes,
            confidence=1.0,
            novelty=novelty,
            urgency=urgency,
            metadata={
                "url": after.url,
                "title": after.title,
                "text_change_ratio": round(text_delta, 6),
            },
            tags=tags,
        )

    @staticmethod
    def _summary(before: BrowserSnapshot, after: BrowserSnapshot, tags: list[str]) -> str:
        if "navigation" in tags:
            return f"Browser navigated: {before.url} -> {after.url}"
        if "title" in tags and "content" not in tags:
            return f"Browser title changed: {after.title}"
        return f"Browser content changed: {after.title or after.url}"
