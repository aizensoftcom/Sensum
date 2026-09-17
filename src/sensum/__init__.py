"""Sensum: continuous perception without continuous LLM inference."""

from .adapters import AgentAdapter, AgentEventPump, CallbackAgentAdapter
from .attention import (
    AttentionDecision,
    AttentionPolicy,
    BudgetedAttention,
    ThresholdAttention,
)
from .fusion import DEFAULT_RULES, FusionRule, TemporalFusionEngine
from .models import Modality, SensoryEvent, StateChange
from .persistence import SQLiteEventStore
from .plugins import PluginRegistry, registry
from .runtime import RuntimeStats, SensumRuntime
from .world import WorldHistoryEntry, WorldState

__all__ = [
    "DEFAULT_RULES",
    "AgentAdapter",
    "AgentEventPump",
    "AttentionDecision",
    "AttentionPolicy",
    "BudgetedAttention",
    "CallbackAgentAdapter",
    "FusionRule",
    "Modality",
    "PluginRegistry",
    "RuntimeStats",
    "SQLiteEventStore",
    "SensoryEvent",
    "SensumRuntime",
    "StateChange",
    "TemporalFusionEngine",
    "ThresholdAttention",
    "WorldHistoryEntry",
    "WorldState",
    "registry",
]

__version__ = "0.3.0a1"
