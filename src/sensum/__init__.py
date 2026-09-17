"""Sensum: continuous perception without continuous LLM inference."""

from .attention import AttentionDecision, AttentionPolicy, ThresholdAttention
from .fusion import DEFAULT_RULES, FusionRule, TemporalFusionEngine
from .models import Modality, SensoryEvent, StateChange
from .persistence import SQLiteEventStore
from .runtime import RuntimeStats, SensumRuntime
from .world import WorldHistoryEntry, WorldState

__all__ = [
    "AttentionDecision",
    "AttentionPolicy",
    "DEFAULT_RULES",
    "FusionRule",
    "Modality",
    "RuntimeStats",
    "SQLiteEventStore",
    "SensoryEvent",
    "SensumRuntime",
    "StateChange",
    "TemporalFusionEngine",
    "ThresholdAttention",
    "WorldHistoryEntry",
    "WorldState",
]

__version__ = "0.3.0a1"
