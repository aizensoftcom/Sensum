from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta

from .models import Modality, SensoryEvent


@dataclass(slots=True)
class FusionRule:
    name: str
    required_kinds: set[str]
    output_kind: str
    summary: str
    window_seconds: float = 5.0
    novelty: float = 0.85
    urgency: float = 0.4
    tags: list[str] = field(default_factory=lambda: ["fused"])


class TemporalFusionEngine:
    """Correlate semantic events across modalities inside a short time window.

    This is intentionally deterministic. Learned/LLM fusion can be added later without changing
    the contract used by callers.
    """

    def __init__(self, rules: list[FusionRule] | None = None, max_events: int = 512) -> None:
        self.rules = rules or []
        self._events: deque[SensoryEvent] = deque(maxlen=max_events)
        self._seen_event_ids: set[str] = set()
        self._emitted_signatures: set[tuple[str, tuple[str, ...]]] = set()

    def add_rule(self, rule: FusionRule) -> None:
        self.rules.append(rule)

    def observe(self, event: SensoryEvent) -> list[SensoryEvent]:
        if event.id in self._seen_event_ids:
            return []

        if self._events.maxlen is not None and len(self._events) == self._events.maxlen:
            oldest = self._events[0]
            self._seen_event_ids.discard(oldest.id)
        self._events.append(event)
        self._seen_event_ids.add(event.id)

        fused: list[SensoryEvent] = []
        for rule in self.rules:
            window_start = event.occurred_at - timedelta(seconds=rule.window_seconds)
            matching = [
                item
                for item in self._events
                if item.occurred_at >= window_start and item.kind in rule.required_kinds
            ]
            kinds = {item.kind for item in matching}
            if not rule.required_kinds.issubset(kinds):
                continue
            source_ids = tuple(
                sorted({item.id for item in matching if item.kind in rule.required_kinds})
            )
            signature = (rule.name, source_ids)
            if signature in self._emitted_signatures:
                continue
            self._emitted_signatures.add(signature)
            modalities = sorted({item.modality.value for item in matching})
            entities = sorted({item.entity for item in matching if item.entity})
            fused.append(
                SensoryEvent(
                    kind=rule.output_kind,
                    source="fusion",
                    modality=Modality.CUSTOM,
                    summary=rule.summary,
                    entity=entities[0] if len(entities) == 1 else None,
                    confidence=min(item.confidence for item in matching),
                    novelty=rule.novelty,
                    urgency=rule.urgency,
                    metadata={
                        "rule": rule.name,
                        "source_event_ids": list(source_ids),
                        "modalities": modalities,
                        "entities": entities,
                    },
                    tags=list(rule.tags),
                )
            )
        return fused


DEFAULT_RULES = [
    FusionRule(
        name="voice-browser-action",
        required_kinds={"speech.started", "browser.navigated"},
        output_kind="user.cross_modal_action",
        summary="User speech and browser navigation occurred in the same attention window",
        window_seconds=4.0,
        novelty=0.88,
        urgency=0.45,
        tags=["fused", "multimodal", "attention"],
    ),
    FusionRule(
        name="interruption-browser-change",
        required_kinds={"user.interrupted_agent", "browser.changed"},
        output_kind="conversation.context_shift",
        summary="User interruption coincided with a browser state change",
        window_seconds=5.0,
        novelty=0.96,
        urgency=0.85,
        tags=["fused", "interrupt", "important"],
    ),
]
