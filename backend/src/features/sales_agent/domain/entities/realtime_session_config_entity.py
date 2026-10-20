from dataclasses import dataclass

from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition


@dataclass(frozen=True)
class RealtimeSessionConfig:
    model: str
    voice: str
    system_instruction: str
    tools: list[ToolDefinition]
