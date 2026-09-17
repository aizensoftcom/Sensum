from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from sensum.models import Modality, SensoryEvent, StateChange

from .base import SensorStats


@dataclass(slots=True, frozen=True)
class _FileSnapshot:
    size: int
    mtime_ns: int


class FileSensor:
    """Portable polling file sensor with no third-party dependencies."""

    def __init__(
        self,
        root: str | Path,
        *,
        interval: float = 0.75,
        recursive: bool = True,
        include_hidden: bool = False,
        name: str = "files",
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.interval = interval
        self.recursive = recursive
        self.include_hidden = include_hidden
        self.name = name
        self.stats = SensorStats()
        self._previous: dict[Path, _FileSnapshot] | None = None

    async def events(self) -> AsyncIterator[SensoryEvent]:
        if not self.root.exists():
            raise FileNotFoundError(self.root)
        while True:
            current = self._scan()
            self.stats.raw_observations += 1
            if self._previous is not None:
                for path in sorted(current.keys() - self._previous.keys()):
                    snapshot = current[path]
                    self.stats.semantic_events += 1
                    yield self._created(path, snapshot)
                for path in sorted(self._previous.keys() - current.keys()):
                    self.stats.semantic_events += 1
                    yield self._deleted(path, self._previous[path])
                for path in sorted(current.keys() & self._previous.keys()):
                    before, after = self._previous[path], current[path]
                    if before != after:
                        self.stats.semantic_events += 1
                        yield self._modified(path, before, after)
            self._previous = current
            await asyncio.sleep(self.interval)

    def _scan(self) -> dict[Path, _FileSnapshot]:
        pattern = "**/*" if self.recursive else "*"
        result: dict[Path, _FileSnapshot] = {}
        for path in self.root.glob(pattern):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if not self.include_hidden and any(part.startswith(".") for part in rel.parts):
                continue
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            result[rel] = _FileSnapshot(size=stat.st_size, mtime_ns=stat.st_mtime_ns)
        return result

    def _entity(self, path: Path) -> str:
        return f"file:{path.as_posix()}"

    def _created(self, path: Path, snap: _FileSnapshot) -> SensoryEvent:
        return SensoryEvent(
            kind="file.created",
            source=self.name,
            modality=Modality.FILE,
            entity=self._entity(path),
            summary=f"File created: {path.as_posix()}",
            changes=[
                StateChange("exists", False, True),
                StateChange("size", None, snap.size),
                StateChange("mtime_ns", None, snap.mtime_ns),
            ],
            novelty=0.9,
            urgency=0.15,
            metadata={"path": path.as_posix()},
            tags=["created"],
        )

    def _modified(self, path: Path, before: _FileSnapshot, after: _FileSnapshot) -> SensoryEvent:
        return SensoryEvent(
            kind="file.modified",
            source=self.name,
            modality=Modality.FILE,
            entity=self._entity(path),
            summary=f"File modified: {path.as_posix()}",
            changes=[
                StateChange("size", before.size, after.size),
                StateChange("mtime_ns", before.mtime_ns, after.mtime_ns),
            ],
            novelty=0.72,
            urgency=0.10,
            metadata={"path": path.as_posix()},
            tags=["modified"],
        )

    def _deleted(self, path: Path, before: _FileSnapshot) -> SensoryEvent:
        return SensoryEvent(
            kind="file.deleted",
            source=self.name,
            modality=Modality.FILE,
            entity=self._entity(path),
            summary=f"File deleted: {path.as_posix()}",
            changes=[
                StateChange("exists", True, False),
                StateChange("size", before.size, None),
            ],
            novelty=0.95,
            urgency=0.45,
            metadata={"path": path.as_posix()},
            tags=["deleted"],
        )
