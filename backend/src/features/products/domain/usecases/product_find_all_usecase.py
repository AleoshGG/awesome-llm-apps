from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.repositories.product_repository import ProductRepository


class ProductFindAllUseCase:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[ProductDetail]:
        return await self._repository.find_all()
