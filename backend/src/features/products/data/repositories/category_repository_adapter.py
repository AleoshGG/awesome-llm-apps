from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.products.data.mappers.category_mapper import CategoryMapper
from src.features.products.data.models.category_model import CategoryModel
from src.features.products.domain.entities.category_entity import Category
from src.features.products.domain.repositories.category_repository import CategoryRepository


class CategoryRepositoryAdapter(CategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Category]:
        stmt = select(CategoryModel)
        result = await self._session.scalars(stmt)
        models = result.all()
        return [CategoryMapper.to_domain(model) for model in models]
