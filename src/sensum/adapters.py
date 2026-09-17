from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from .models import SensoryEvent


class AgentAdapter(Protocol):
    """Minimal contract for forwarding significant Sensum events to any agent runtime."""

    async def handle(self, event: SensoryEvent) -> None: ...


class CallbackAgentAdapter:
    """Provider-neutral adapter for OpenAI, Anthropic, Gemini, Ollama or custom agents.

    Keeping the core callback-based avoids forcing provider SDKs into Sensum's dependency graph.
    Provider-specific packages can wrap this contract in separate integrations.
    """

    def __init__(self, callback: Callable[[SensoryEvent], Awaitable[None]]) -> None:
        self.callback = callback

    async def handle(self, event: SensoryEvent) -> None:
        await self.callback(event)


class AgentEventPump:
    """Consume runtime events and forward them to one or more agent adapters."""

    def __init__(self, *adapters: AgentAdapter) -> None:
        self.adapters = list(adapters)

    async def run(self, events) -> None:
        async for event in events:
            for adapter in self.adapters:
                await adapter.handle(event)
