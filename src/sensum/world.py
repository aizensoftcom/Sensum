from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any

from .models import SensoryEvent


class WorldState:
    """Small canonical state store updated by semantic deltas."""

    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def apply(self, event: SensoryEvent) -> None:
        if not event.entity or not event.changes:
            return
        with self._lock:
            entity = self._entities.setdefault(event.entity, {})
            for change in event.changes:
                _set_path(entity, change.path, deepcopy(change.after))

    def get(self, entity: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._entities.get(entity)
            return deepcopy(value) if value is not None else None

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return deepcopy(self._entities)

    def clear(self) -> None:
        with self._lock:
            self._entities.clear()


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
