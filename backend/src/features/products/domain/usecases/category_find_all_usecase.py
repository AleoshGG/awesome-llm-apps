from src.features.products.domain.entities.category_entity import Category
from src.features.products.domain.repositories.category_repository import CategoryRepository


class CategoryFindAllUseCase:
    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Category]:
        return await self._repository.find_all()
