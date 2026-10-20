from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from src.features.sales_agent.domain.entities.agent_event_entity import AgentEvent
from src.features.sales_agent.domain.entities.realtime_session_config_entity import RealtimeSessionConfig
from src.features.sales_agent.domain.entities.tool_result_entity import ToolResult


class RealtimeVoiceSession(Protocol):
    async def send_audio(self, data: bytes) -> None: ...

    async def send_text(self, text: str) -> None: ...

    async def send_tool_result(self, result: ToolResult) -> None: ...

    def events(self) -> AsyncIterator[AgentEvent]: ...

    async def close(self) -> None: ...


class RealtimeVoiceService(Protocol):
    def connect(
        self, config: RealtimeSessionConfig
    ) -> AbstractAsyncContextManager[RealtimeVoiceSession]: ...
