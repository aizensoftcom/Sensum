from __future__ import annotations

import asyncio

import pytest

from sensum.sensors import BrowserSensor, BrowserSnapshot


@pytest.mark.asyncio
async def test_browser_sensor_emits_navigation_delta() -> None:
    snapshots = iter(
        [
            BrowserSnapshot("https://example.test/a", "A", "hello"),
            BrowserSnapshot("https://example.test/b", "B", "hello world"),
        ]
    )

    async def provider() -> BrowserSnapshot:
        try:
            return next(snapshots)
        except StopIteration:
            await asyncio.sleep(10)
            raise AssertionError("unreachable")

    sensor = BrowserSensor(provider, interval=0, text_change_threshold=0.01)
    event = await asyncio.wait_for(anext(sensor.events()), timeout=1)

    assert event.kind == "browser.navigated"
    assert event.modality.value == "browser"
    assert sensor.stats.raw_observations == 2
    assert sensor.stats.semantic_events == 1
