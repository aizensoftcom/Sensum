from sensum.sensors.vision import VisionEventSensor, VisionObservation


def test_vision_sensor_compares_local_cv_observations() -> None:
    async def provider() -> VisionObservation:
        return VisionObservation()

    sensor = VisionEventSensor(provider, motion_threshold=0.25)
    before = VisionObservation(objects=frozenset(), motion_score=0.0, scene="door")
    after = VisionObservation(
        objects=frozenset({"person"}), motion_score=0.8, scene="door"
    )

    events = sensor._compare(before, after)
    kinds = {event.kind for event in events}
    assert "vision.object_entered" in kinds
    assert "vision.motion_started" in kinds
