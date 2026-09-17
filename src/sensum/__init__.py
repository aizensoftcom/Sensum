"""Sensum: continuous perception without continuous LLM inference."""

from .attention import AttentionDecision, AttentionPolicy, ThresholdAttention
from .models import Modality, SensoryEvent, StateChange
from .runtime import RuntimeStats, SensumRuntime
from .world import WorldState

__all__ = [
    "AttentionDecision",
    "AttentionPolicy",
    "Modality",
    "RuntimeStats",
    "SensoryEvent",
    "SensumRuntime",
    "StateChange",
    "ThresholdAttention",
    "WorldState",
]

__version__ = "0.2.0a1"
