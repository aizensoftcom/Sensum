from fastapi.testclient import TestClient

from sensum.gateway import create_app


def test_gateway_health_stats_and_ingest() -> None:
    app = create_app()

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        before = client.get("/stats").json()
        assert before["totals"]["reasoning_events"] == 0

        response = client.post(
            "/ingest",
            json={
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

        world = client.get("/world").json()
        assert world["payment:1"]["status"] == "completed"

        after = client.get("/stats").json()
        assert after["runtime"]["emitted"] == 1
