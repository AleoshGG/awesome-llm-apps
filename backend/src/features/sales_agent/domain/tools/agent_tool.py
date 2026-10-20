from abc import ABC, abstractmethod

from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition


class AgentTool(ABC):
    # Cart reads also wait for preceding mutations to return a consistent view.
    uses_cart: bool = False

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(self, args: dict) -> dict:
        pass
