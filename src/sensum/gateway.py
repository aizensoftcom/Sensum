import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from .dashboard import DASHBOARD_HTML
from .models import Modality, SensoryEvent, StateChange
from .runtime import SensumRuntime


def _parse_occurred_at(value: Any) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _event_from_payload(payload: dict[str, Any]) -> SensoryEvent:
    changes = [
        StateChange(
            path=str(change.get("path", "state")),
            before=change.get("before"),
            after=change.get("after"),
        )
        for change in payload.get("changes", [])
    ]
    identity: dict[str, Any] = {}
    if payload.get("id") is not None:
        identity["id"] = str(payload["id"])
    if payload.get("occurred_at") is not None:
        identity["occurred_at"] = _parse_occurred_at(payload["occurred_at"])
    return SensoryEvent(
        kind=str(payload["kind"]),
        source=str(payload.get("source", "gateway")),
        modality=Modality(str(payload.get("modality", "custom"))),
        summary=str(payload.get("summary", payload["kind"])),
        entity=payload.get("entity"),
        changes=changes,
        confidence=float(payload.get("confidence", 1.0)),
        novelty=float(payload.get("novelty", 0.5)),
        urgency=float(payload.get("urgency", 0.0)),
        metadata=dict(payload.get("metadata", {})),
        tags=list(payload.get("tags", [])),
        **identity,
    )


def create_app(runtime: SensumRuntime | None = None):
    """Create the optional FastAPI gateway for events, state, replay and live UI."""

    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import HTMLResponse, StreamingResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Sensum gateway dependencies are not installed. "
            "Install with: pip install -e '.[server]'"
        ) from exc

    runtime = runtime or SensumRuntime()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await runtime.start()
        try:
            yield
        finally:
            await runtime.stop()

    app = FastAPI(
        title="Sensum Gateway",
        version="0.3.0a1",
        description="Live sensory-event gateway for Sensum.",
        lifespan=lifespan,
    )

    @app.get("/", response_class=HTMLResponse)
    async def dashboard() -> str:
        return DASHBOARD_HTML

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/stats")
    async def stats() -> dict[str, Any]:
        return runtime.metrics()

    @app.get("/world")
    async def world() -> dict[str, Any]:
        return runtime.world.snapshot()

    @app.get("/world/history")
    async def world_history(
        entity: str | None = None,
        path: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return [
            {**asdict(item), "occurred_at": item.occurred_at.isoformat()}
            for item in runtime.world.history(entity=entity, path=path, limit=min(limit, 1000))
        ]

    @app.get("/replay")
    async def replay(
        after_seq: int = 0,
        limit: int = 100,
        entity: str | None = None,
        kind: str | None = None,
    ) -> list[dict[str, Any]]:
        store = runtime.store
        if store is None or not hasattr(store, "replay"):
            return []
        events = store.replay(  # type: ignore[attr-defined]
            after_seq=after_seq,
            limit=min(limit, 1000),
            entity=entity,
            kind=kind,
        )
        return [event.to_dict() for event in events]

    @app.post("/ingest")
    async def ingest(payload: dict[str, Any]) -> dict[str, Any]:
        event = _event_from_payload(payload)
        emitted = await runtime.ingest(event)
        return {"emitted": emitted, "event": event.to_dict()}

    @app.get("/events")
    async def events():
        async def stream():
            yield ": sensum connected\n\n"
            async for event in runtime.events():
                data = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
                yield f"event: sensory\ndata: {data}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.websocket("/ws")
    async def websocket_events(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            async for event in runtime.events():
                await websocket.send_json(event.to_dict())
        except WebSocketDisconnect:
            return

    app.state.sensum_runtime = runtime
    return app
