from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class Modality(StrEnum):
    VISION = "vision"
    AUDIO = "audio"
    SCREEN = "screen"
    BROWSER = "browser"
    FILE = "file"
    API = "api"
    SENSOR = "sensor"
    CUSTOM = "custom"


@dataclass(slots=True, frozen=True)
class StateChange:
    """One state transition caused or observed by a sensory event."""

    path: str
    before: Any = None
    after: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SensoryEvent:
    """Canonical event passed through the Sensum runtime.

    Sensors should emit small semantic deltas rather than raw continuous media whenever possible.
    Raw payloads may be referenced in ``metadata`` but are intentionally not required by the protocol.
    """

    kind: str
    source: str
    modality: Modality | str
    summary: str
    entity: str | None = None
    changes: list[StateChange] = field(default_factory=list)
    confidence: float = 1.0
    novelty: float = 0.5
    urgency: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        self.confidence = _bounded(self.confidence, "confidence")
        self.novelty = _bounded(self.novelty, "novelty")
        self.urgency = _bounded(self.urgency, "urgency")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if isinstance(self.modality, str):
            self.modality = Modality(self.modality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "occurred_at": self.occurred_at.isoformat(),
            "kind": self.kind,
            "source": self.source,
            "modality": self.modality.value,
            "summary": self.summary,
            "entity": self.entity,
            "changes": [change.to_dict() for change in self.changes],
            "confidence": self.confidence,
            "novelty": self.novelty,
            "urgency": self.urgency,
            "metadata": self.metadata,
            "tags": self.tags,
        }


def _bounded(value: float, field_name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return value
