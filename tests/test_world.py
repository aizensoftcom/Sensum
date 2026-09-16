from sensum import Modality, SensoryEvent, StateChange, WorldState


def test_world_applies_nested_changes() -> None:
    world = WorldState()
    event = SensoryEvent(kind="object.moved", source="camera", modality=Modality.VISION, entity="object:keys", summary="Keys moved", changes=[StateChange("location.room", "kitchen", "hall")])
    world.apply(event)
    assert world.get("object:keys") == {"location": {"room": "hall"}}
