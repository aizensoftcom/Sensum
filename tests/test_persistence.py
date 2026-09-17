from sensum import Modality, SensoryEvent, StateChange
from sensum.persistence import SQLiteEventStore


def test_sqlite_event_store_roundtrip(tmp_path) -> None:
    store = SQLiteEventStore(tmp_path / "sensum.db")
    event = SensoryEvent(
        kind="payment.completed",
        source="test",
        modality=Modality.API,
        summary="Payment completed",
        entity="payment:1",
        changes=[StateChange("status", "pending", "completed")],
        novelty=0.9,
        urgency=0.8,
        tags=["payment"],
    )

    store.append(event)
    replayed = list(store.replay(entity="payment:1"))

    assert store.count() == 1
    assert len(replayed) == 1
    assert replayed[0].id == event.id
    assert replayed[0].changes[0].after == "completed"
    store.close()
