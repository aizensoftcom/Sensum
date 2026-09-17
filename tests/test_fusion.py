from datetime import timedelta

from sensum.fusion import FusionRule, TemporalFusionEngine
from sensum.models import Modality, SensoryEvent


def test_temporal_fusion_emits_once_when_rule_matches() -> None:
    engine = TemporalFusionEngine(
        [
            FusionRule(
                name="speech-nav",
                required_kinds={"speech.started", "browser.navigated"},
                output_kind="user.cross_modal_action",
                summary="Cross-modal action",
            )
        ]
    )
    first = SensoryEvent(
        kind="speech.started",
        source="audio",
        modality=Modality.AUDIO,
        summary="Speech started",
    )
    second = SensoryEvent(
        kind="browser.navigated",
        source="browser",
        modality=Modality.BROWSER,
        summary="Browser navigated",
        occurred_at=first.occurred_at + timedelta(seconds=1),
    )

    assert engine.observe(first) == []
    fused = engine.observe(second)
    assert len(fused) == 1
    assert fused[0].kind == "user.cross_modal_action"
    assert set(fused[0].metadata["modalities"]) == {"audio", "browser"}
    assert engine.observe(second) == []
