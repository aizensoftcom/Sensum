from sensum import Modality, SensoryEvent, SensumRuntime
from sensum.fusion import DEFAULT_RULES, TemporalFusionEngine


async def test_trace_records_filtered_and_published_events() -> None:
    runtime = SensumRuntime()

    quiet = SensoryEvent(
        kind="ambient.noise",
        source="test",
        modality=Modality.AUDIO,
        summary="background noise",
        confidence=0.95,
        novelty=0.02,
        urgency=0.0,
    )
    important = SensoryEvent(
        kind="payment.completed",
        source="test",
        modality=Modality.API,
        summary="payment completed",
        confidence=0.99,
        novelty=0.98,
        urgency=0.9,
        tags=["payment"],
    )

    assert await runtime.ingest(quiet) is False
    assert await runtime.ingest(important) is True

    traces = runtime.trace.recent()
    assert traces[0].event_id == important.id
    assert traces[0].significant is True
    assert traces[0].published is True
    assert traces[1].event_id == quiet.id
    assert traces[1].significant is False
    assert traces[1].published is False


async def test_trace_preserves_fusion_provenance() -> None:
    runtime = SensumRuntime(fusion=TemporalFusionEngine(list(DEFAULT_RULES)))
    speech = SensoryEvent(
        kind="speech.started",
        source="audio",
        modality=Modality.AUDIO,
        summary="speech started",
        confidence=0.98,
        novelty=0.3,
        urgency=0.1,
    )
    navigation = SensoryEvent(
        kind="browser.navigated",
        source="browser",
        modality=Modality.BROWSER,
        summary="navigated",
        confidence=0.99,
        novelty=0.8,
        urgency=0.3,
    )

    await runtime.ingest(speech)
    await runtime.ingest(navigation)

    fused = [item for item in runtime.trace.recent() if item.fused]
    assert fused
    assert fused[0].kind == "user.cross_modal_action"
    assert speech.id in fused[0].parent_event_ids
    assert navigation.id in fused[0].parent_event_ids
