from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition
from src.features.sales_agent.domain.exceptions import ToolNotFoundError
from src.features.sales_agent.domain.tools.agent_tool import AgentTool


class ToolRegistry:
    def __init__(self, tools: list[AgentTool]) -> None:
        self._tools = {tool.definition.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Duplicate tool names")

    def get(self, name: str) -> AgentTool:
        try:
            return self._tools[name]
        except KeyError:
            raise ToolNotFoundError("Herramienta desconocida") from None

    def definitions(self) -> list[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]
