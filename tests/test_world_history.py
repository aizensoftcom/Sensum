from sensum.models import Modality, SensoryEvent, StateChange
from sensum.world import WorldState


def test_world_state_tracks_history_and_values() -> None:
    world = WorldState()
    world.apply(
        SensoryEvent(
            kind="payment.changed",
            source="test",
            modality=Modality.API,
            summary="Payment changed",
            entity="payment:1",
            changes=[StateChange("status", "pending", "completed")],
        )
    )

    assert world.value("payment:1", "status") == "completed"
    history = world.history(entity="payment:1", path="status")
    assert len(history) == 1
    assert history[0].before == "pending"
    assert history[0].after == "completed"
