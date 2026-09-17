from datetime import timedelta

from sensum.attention import BudgetedAttention, ThresholdAttention
from sensum.models import Modality, SensoryEvent


def _event(*, urgency: float, seconds: int) -> SensoryEvent:
    base = SensoryEvent(
        kind="alarm.change",
        source="test",
        modality=Modality.SENSOR,
        summary="Change",
        novelty=0.95,
        urgency=urgency,
        confidence=1.0,
        tags=["alarm"],
    )
    base.occurred_at = base.occurred_at + timedelta(seconds=seconds)
    return base


def test_attention_budget_limits_normal_events_but_allows_urgent_bypass() -> None:
    policy = BudgetedAttention(
        ThresholdAttention(threshold=0.55), max_events=2, window_seconds=60, bypass_urgency=0.9
    )

    assert policy.assess(_event(urgency=0.6, seconds=0)).significant
    assert policy.assess(_event(urgency=0.6, seconds=1)).significant
    blocked = policy.assess(_event(urgency=0.6, seconds=2))
    urgent = policy.assess(_event(urgency=0.95, seconds=3))

    assert not blocked.significant
    assert "attention_budget_exhausted" in blocked.reasons
    assert urgent.significant
    assert "budget_bypass=urgent" in urgent.reasons
