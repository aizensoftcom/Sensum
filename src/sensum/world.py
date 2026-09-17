from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Any

from .models import SensoryEvent


@dataclass(slots=True, frozen=True)
class WorldHistoryEntry:
    occurred_at: datetime
    event_id: str
    entity: str
    path: str
    before: Any
    after: Any


class WorldState:
    """Canonical world state plus an in-memory transition history."""

    def __init__(self, *, history_limit: int = 10_000) -> None:
        self._entities: dict[str, dict[str, Any]] = {}
        self._history: list[WorldHistoryEntry] = []
        self._history_limit = history_limit
        self._lock = RLock()

    def apply(self, event: SensoryEvent) -> None:
        if not event.entity or not event.changes:
            return
        with self._lock:
            entity = self._entities.setdefault(event.entity, {})
            for change in event.changes:
                before = deepcopy(_get_path(entity, change.path))
                _set_path(entity, change.path, deepcopy(change.after))
                self._history.append(
                    WorldHistoryEntry(
                        occurred_at=event.occurred_at,
                        event_id=event.id,
                        entity=event.entity,
                        path=change.path,
                        before=before if before is not None else deepcopy(change.before),
                        after=deepcopy(change.after),
                    )
                )
            if len(self._history) > self._history_limit:
                del self._history[: len(self._history) - self._history_limit]

    def get(self, entity: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._entities.get(entity)
            return deepcopy(value) if value is not None else None

    def value(self, entity: str, path: str, default: Any = None) -> Any:
        with self._lock:
            value = self._entities.get(entity)
            if value is None:
                return deepcopy(default)
            result = _get_path(value, path)
            return deepcopy(default if result is None else result)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return deepcopy(self._entities)

    def history(
        self,
        *,
        entity: str | None = None,
        path: str | None = None,
        limit: int = 100,
    ) -> list[WorldHistoryEntry]:
        with self._lock:
            items = self._history
            if entity is not None:
                items = [item for item in items if item.entity == entity]
            if path is not None:
                items = [item for item in items if item.path == path]
            return list(deepcopy(items[-limit:]))

    def clear(self) -> None:
        with self._lock:
            self._entities.clear()
            self._history.clear()


def _get_path(target: dict[str, Any], path: str) -> Any:
    parts = [part for part in path.split(".") if part]
    if not parts:
        raise ValueError("state path must not be empty")
    cursor: Any = target
    for part in parts:
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


def _set_path(target: dict[str, Any], path: str, value: Any) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        raise ValueError("state change path must not be empty")
    cursor = target
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[part] = next_value
        cursor = next_value
    cursor[parts[-1]] = value
