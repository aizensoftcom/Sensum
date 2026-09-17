from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from threading import RLock
from typing import Any

from .models import Modality, SensoryEvent, StateChange


class SQLiteEventStore:
    """Small dependency-free event log for replay, debugging and audits."""

    def __init__(self, path: str | Path = "sensum.db") -> None:
        self.path = str(path)
        self._lock = RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                occurred_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                source TEXT NOT NULL,
                modality TEXT NOT NULL,
                entity TEXT,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_entity_seq ON events(entity, seq)"
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_kind_seq ON events(kind, seq)"
        )
        self._connection.commit()

    def append(self, event: SensoryEvent) -> int:
        payload = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            cursor = self._connection.execute(
                """
                INSERT OR IGNORE INTO events
                    (event_id, occurred_at, kind, source, modality, entity, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.occurred_at.isoformat(),
                    event.kind,
                    event.source,
                    event.modality.value,
                    event.entity,
                    payload,
                ),
            )
            self._connection.commit()
            return int(cursor.lastrowid or 0)

    def replay(
        self,
        *,
        after_seq: int = 0,
        limit: int = 100,
        entity: str | None = None,
        kind: str | None = None,
    ) -> Iterator[SensoryEvent]:
        clauses = ["seq > ?"]
        params: list[Any] = [after_seq]
        if entity is not None:
            clauses.append("entity = ?")
            params.append(entity)
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        params.append(limit)
        query = (
            "SELECT payload FROM events WHERE "
            + " AND ".join(clauses)
            + " ORDER BY seq ASC LIMIT ?"
        )
        with self._lock:
            rows = list(self._connection.execute(query, params))
        for (payload,) in rows:
            yield _event_from_dict(json.loads(payload))

    def recent(self, limit: int = 100) -> list[SensoryEvent]:
        with self._lock:
            rows = list(
                self._connection.execute(
                    "SELECT payload FROM events ORDER BY seq DESC LIMIT ?", (limit,)
                )
            )
        return [_event_from_dict(json.loads(payload)) for (payload,) in reversed(rows)]

    def count(self) -> int:
        with self._lock:
            row = self._connection.execute("SELECT COUNT(*) FROM events").fetchone()
        return int(row[0] if row else 0)

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def _event_from_dict(data: dict[str, Any]) -> SensoryEvent:
    from datetime import datetime

    return SensoryEvent(
        id=str(data["id"]),
        occurred_at=datetime.fromisoformat(str(data["occurred_at"])),
        kind=str(data["kind"]),
        source=str(data["source"]),
        modality=Modality(str(data["modality"])),
        summary=str(data.get("summary", data["kind"])),
        entity=data.get("entity"),
        changes=[
            StateChange(
                path=str(change["path"]),
                before=change.get("before"),
                after=change.get("after"),
            )
            for change in data.get("changes", [])
        ],
        confidence=float(data.get("confidence", 1.0)),
        novelty=float(data.get("novelty", 0.5)),
        urgency=float(data.get("urgency", 0.0)),
        metadata=dict(data.get("metadata", {})),
        tags=list(data.get("tags", [])),
    )
