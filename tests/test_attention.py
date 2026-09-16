from sensum import Modality, SensoryEvent, ThresholdAttention


def test_noise_is_suppressed() -> None:
    policy = ThresholdAttention(threshold=0.55)
    event = SensoryEvent(kind="screen.minor_change", source="screen", modality=Modality.SCREEN, summary="Mouse moved slightly", novelty=0.10, urgency=0.0, confidence=1.0)
    assert policy.assess(event).significant is False


def test_urgent_event_passes() -> None:
    policy = ThresholdAttention(threshold=0.55)
    event = SensoryEvent(kind="alarm.started", source="room", modality=Modality.SENSOR, summary="Smoke alarm started", novelty=1.0, urgency=1.0, confidence=0.95, tags=["alarm"])
    decision = policy.assess(event)
    assert decision.significant is True
    assert decision.score > 0.9
