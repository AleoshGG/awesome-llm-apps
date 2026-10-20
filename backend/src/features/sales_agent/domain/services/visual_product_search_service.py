from typing import Protocol

from src.features.sales_agent.domain.entities.client_input_entity import ClientImage
from src.features.sales_agent.domain.entities.visual_search_result_entity import VisualSearchResult


class VisualProductSearchService(Protocol):
    async def analyze(self, image: ClientImage) -> VisualSearchResult: ...
