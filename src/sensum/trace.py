from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from .models import SensoryEvent


@dataclass(slots=True, frozen=True)
class PerceptionTrace:
    """Inspectable record of one event's path through the Sensum runtime."""

    event_id: str
    occurred_at: str
    processed_at: str
    kind: str
    source: str
    modality: str
    entity: str | None
    attention_score: float
    significant: bool
    attention_reasons: tuple[str, ...]
    persisted: bool
    published: bool
    fused: bool
    parent_event_ids: tuple[str, ...]
    changes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TraceBuffer:
    """Small in-memory perception trace for debugging and explainability.

    The trace stores semantic metadata only; it does not retain raw audio, video or screen data.
    """

    def __init__(self, maxlen: int = 2_000) -> None:
        if maxlen < 1:
            raise ValueError("maxlen must be >= 1")
        self._records: deque[PerceptionTrace] = deque(maxlen=maxlen)
        self._by_id: dict[str, PerceptionTrace] = {}
        self._lock = RLock()

    def record(
        self,
        event: SensoryEvent,
        *,
        attention_score: float,
        significant: bool,
        attention_reasons: tuple[str, ...],
        persisted: bool,
        published: bool,
    ) -> PerceptionTrace:
        parent_ids = tuple(str(item) for item in event.metadata.get("source_event_ids", []))
        trace = PerceptionTrace(
            event_id=event.id,
            occurred_at=event.occurred_at.isoformat(),
            processed_at=datetime.now(UTC).isoformat(),
            kind=event.kind,
            source=event.source,
            modality=event.modality.value,
            entity=event.entity,
            attention_score=round(float(attention_score), 5),
            significant=bool(significant),
            attention_reasons=tuple(attention_reasons),
            persisted=bool(persisted),
            published=bool(published),
            fused=event.source == "fusion" or bool(parent_ids),
            parent_event_ids=parent_ids,
            changes=len(event.changes),
        )
        with self._lock:
            if len(self._records) == self._records.maxlen and self._records:
                self._by_id.pop(self._records[0].event_id, None)
            self._records.append(trace)
            self._by_id[trace.event_id] = trace
        return trace

    def recent(
        self,
        *,
        limit: int = 100,
        significant: bool | None = None,
        kind: str | None = None,
    ) -> list[PerceptionTrace]:
        limit = max(0, min(int(limit), 1_000))
        with self._lock:
            records = list(reversed(self._records))
        if significant is not None:
            records = [item for item in records if item.significant is significant]
        if kind is not None:
            records = [item for item in records if item.kind == kind]
        return records[:limit]

    def get(self, event_id: str) -> PerceptionTrace | None:
        with self._lock:
            return self._by_id.get(event_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)
