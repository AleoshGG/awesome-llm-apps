from abc import ABC, abstractmethod

from src.features.sales.domain.entities.sale_entity import Sale


class SaleRepository(ABC):
    @abstractmethod
    async def register(self) -> Sale:
        pass

    @abstractmethod
    async def find_all(self) -> list[Sale]:
        pass
