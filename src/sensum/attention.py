from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta
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
    kind_boosts: dict[str, float] = field(
        default_factory=lambda: {
            "error": 0.25,
            "failed": 0.25,
            "deleted": 0.18,
            "created": 0.08,
            "started": 0.05,
            "stopped": 0.05,
            "payment": 0.20,
            "alarm": 0.30,
            "interrupt": 0.18,
        }
    )

    def assess(self, event: SensoryEvent) -> AttentionDecision:
        base = (
            event.novelty * self.novelty_weight
            + event.urgency * self.urgency_weight
            + event.confidence * self.confidence_weight
        )
        reasons = [
            f"novelty={event.novelty:.2f}",
            f"urgency={event.urgency:.2f}",
            f"confidence={event.confidence:.2f}",
        ]
        haystack = f"{event.kind} {' '.join(event.tags)}".lower()
        boost = max(
            (value for token, value in self.kind_boosts.items() if token in haystack),
            default=0.0,
        )
        if boost:
            reasons.append(f"kind_boost=+{boost:.2f}")
        score = min(1.0, base + boost)
        return AttentionDecision(
            score=score,
            significant=score >= self.threshold,
            reasons=tuple(reasons),
        )


class BudgetedAttention:
    """Wrap another policy with a rolling reasoning-event budget.

    Urgent events can bypass the budget so a noisy environment cannot hide an alarm or
    interruption merely because the normal attention quota is exhausted.
    """

    def __init__(
        self,
        policy: AttentionPolicy | None = None,
        *,
        max_events: int = 10,
        window_seconds: float = 60.0,
        bypass_urgency: float = 0.9,
    ) -> None:
        if max_events < 1:
            raise ValueError("max_events must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self.policy = policy or ThresholdAttention()
        self.max_events = max_events
        self.window = timedelta(seconds=window_seconds)
        self.bypass_urgency = bypass_urgency
        self._accepted = deque()

    def assess(self, event: SensoryEvent) -> AttentionDecision:
        decision = self.policy.assess(event)
        if not decision.significant:
            return decision

        cutoff = event.occurred_at - self.window
        while self._accepted and self._accepted[0] < cutoff:
            self._accepted.popleft()

        if event.urgency >= self.bypass_urgency:
            self._accepted.append(event.occurred_at)
            return AttentionDecision(
                score=decision.score,
                significant=True,
                reasons=decision.reasons + ("budget_bypass=urgent",),
            )

        if len(self._accepted) >= self.max_events:
            return AttentionDecision(
                score=decision.score,
                significant=False,
                reasons=decision.reasons + ("attention_budget_exhausted",),
            )

        self._accepted.append(event.occurred_at)
        return AttentionDecision(
            score=decision.score,
            significant=True,
            reasons=decision.reasons + ("attention_budget=accepted",),
        )
