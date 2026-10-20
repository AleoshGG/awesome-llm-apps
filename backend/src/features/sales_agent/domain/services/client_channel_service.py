from typing import Protocol

from src.features.sales_agent.domain.entities.agent_event_entity import AgentEvent
from src.features.sales_agent.domain.entities.client_input_entity import ClientInput


class ClientChannel(Protocol):
    async def receive(self) -> ClientInput: ...

    async def send(self, event: AgentEvent) -> None: ...
