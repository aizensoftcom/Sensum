from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from sensum.models import SensoryEvent


class Sensor(Protocol):
    """A source of semantic sensory events."""

    name: str

    def events(self) -> AsyncIterator[SensoryEvent]: ...
