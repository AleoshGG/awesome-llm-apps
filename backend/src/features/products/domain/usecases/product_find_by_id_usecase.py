from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.repositories.product_repository import ProductRepository


class ProductFindByIdUseCase:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(self, product_id: str) -> ProductDetail | None:
        return await self._repository.find_by_id(product_id)
