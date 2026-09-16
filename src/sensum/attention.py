from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import SensoryEvent


@dataclass(slots=True, frozen=True)
class AttentionDecision:
    score: float
    significant: bool
    reasons: tuple[str, ...] = ()


class AttentionPolicy(Protocol):
    def assess(self, event: SensoryEvent) -> AttentionDecision: ...


@dataclass(slots=True)
class ThresholdAttention:
    """Deterministic first-line attention gate with no LLM calls."""

    threshold: float = 0.55
    novelty_weight: float = 0.45
    urgency_weight: float = 0.35
    confidence_weight: float = 0.20
    kind_boosts: dict[str, float] = field(default_factory=lambda: {"error": 0.25, "failed": 0.25, "deleted": 0.18, "created": 0.08, "started": 0.05, "stopped": 0.05, "payment": 0.20, "alarm": 0.30, "interrupt": 0.18})

    def assess(self, event: SensoryEvent) -> AttentionDecision:
        base = event.novelty * self.novelty_weight + event.urgency * self.urgency_weight + event.confidence * self.confidence_weight
        reasons = [f"novelty={event.novelty:.2f}", f"urgency={event.urgency:.2f}", f"confidence={event.confidence:.2f}"]
        haystack = f"{event.kind} {' '.join(event.tags)}".lower()
        boost = max((value for token, value in self.kind_boosts.items() if token in haystack), default=0.0)
        if boost:
            reasons.append(f"kind_boost=+{boost:.2f}")
        score = min(1.0, base + boost)
        return AttentionDecision(score=score, significant=score >= self.threshold, reasons=tuple(reasons))
