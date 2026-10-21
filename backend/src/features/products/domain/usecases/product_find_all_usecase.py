from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.repositories.product_repository import ProductRepository


class ProductFindAllUseCase:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ProductDetail]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        if offset is not None and offset < 0:
            raise ValueError("offset must be non-negative")
        return await self._repository.find_all(limit=limit, offset=offset)
