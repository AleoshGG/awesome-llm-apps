from abc import ABC, abstractmethod

from src.features.products.domain.entities.category_entity import Category


class CategoryRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Category]:
        pass
