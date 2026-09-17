from fastapi.testclient import TestClient

from sensum.dashboard import DASHBOARD_HTML
from sensum.gateway import create_app


def test_gateway_health_stats_ingest_and_trace() -> None:
    app = create_app()

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        before = client.get("/stats").json()
        assert before["totals"]["reasoning_events"] == 0

        response = client.post(
            "/ingest",
            json={
                "id": "external-event-42",
                "occurred_at": "2026-09-17T06:00:00Z",
                "kind": "payment.completed",
                "source": "test",
                "modality": "api",
                "summary": "Payment completed",
                "entity": "payment:1",
                "changes": [
                    {"path": "status", "before": "pending", "after": "completed"}
                ],
                "novelty": 0.95,
                "urgency": 0.9,
                "tags": ["payment"],
            },
        )
        payload = response.json()
        assert payload["emitted"] is True
        assert payload["event"]["id"] == "external-event-42"
        assert payload["event"]["occurred_at"] == "2026-09-17T06:00:00+00:00"

        world = client.get("/world").json()
        assert world["payment:1"]["status"] == "completed"

        after = client.get("/stats").json()
        assert after["runtime"]["emitted"] == 1
        assert after["totals"]["perception_traces"] == 1

        traces = client.get("/traces").json()
        assert traces[0]["event_id"] == "external-event-42"
        assert traces[0]["significant"] is True
        assert traces[0]["published"] is True
        assert traces[0]["attention_score"] > 0.9

        trace = client.get("/traces/external-event-42").json()
        assert trace["kind"] == "payment.completed"
        assert trace["attention_reasons"]
        assert client.get("/traces/missing").status_code == 404


def test_dashboard_does_not_render_event_payload_with_inner_html() -> None:
    assert "row.innerHTML" not in DASHBOARD_HTML
    assert "textContent" in DASHBOARD_HTML
    assert "Perception Trace" in DASHBOARD_HTML
