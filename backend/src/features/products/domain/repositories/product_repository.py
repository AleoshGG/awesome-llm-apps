from abc import ABC, abstractmethod

from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import ProductQuery


class ProductRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[ProductDetail]:
        pass

    @abstractmethod
    async def find_by_id(self, product_id: str) -> ProductDetail | None:
        pass

    @abstractmethod
    async def find_by_query(self, query: ProductQuery) -> list[ProductDetail]:
        pass
