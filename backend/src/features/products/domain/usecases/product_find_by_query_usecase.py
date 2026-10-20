from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.products.domain.repositories.product_repository import ProductRepository


class ProductFindByQueryUseCase:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(self, query: ProductQuery) -> list[ProductDetail]:
        return await self._repository.find_by_query(query)
