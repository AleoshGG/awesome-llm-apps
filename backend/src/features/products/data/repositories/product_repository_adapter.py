from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.features.products.data.mappers.product_mapper import ProductMapper
from src.features.products.data.models.category_model import CategoryModel
from src.features.products.data.models.product_model import ProductModel
from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.products.domain.repositories.product_repository import ProductRepository
from src.features.providers.data.models.provider_model import ProviderModel


class ProductRepositoryAdapter(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_detail_stmt(self) -> Select[tuple[ProductModel]]:
        return (
            select(ProductModel)
            .join(ProductModel.category)
            .join(ProductModel.provider)
            .options(
                joinedload(ProductModel.category),
                joinedload(ProductModel.provider),
                selectinload(ProductModel.media),
            )
        )

    async def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ProductDetail]:
        stmt = self._base_detail_stmt().order_by(ProductModel.id.asc())
        if offset is not None and offset > 0:
            stmt = stmt.offset(offset)
        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        result = await self._session.scalars(stmt)
        models = result.unique().all()
        return [ProductMapper.to_detail_domain(model) for model in models]

    async def find_by_id(self, product_id: str) -> ProductDetail | None:
        stmt = self._base_detail_stmt().where(ProductModel.id == product_id)
        result = await self._session.scalars(stmt)
        model = result.unique().first()
        if model is None:
            return None
        return ProductMapper.to_detail_domain(model)

    async def find_by_query(self, query: ProductQuery) -> list[ProductDetail]:
        stmt = self._base_detail_stmt()

        text_conditions = []
        if query.name and query.name.strip():
            name_pattern = f"%{query.name.strip()}%"
            text_conditions.append(ProductModel.name.ilike(name_pattern))
            text_conditions.append(ProductModel.description.ilike(name_pattern))

        if query.description and query.description.strip():
            desc_pattern = f"%{query.description.strip()}%"
            text_conditions.append(ProductModel.description.ilike(desc_pattern))
            text_conditions.append(ProductModel.name.ilike(desc_pattern))

        if text_conditions:
            stmt = stmt.where(or_(*text_conditions))

        if query.category_name and query.category_name.strip():
            stmt = stmt.where(
                CategoryModel.name.ilike(f"%{query.category_name.strip()}%")
            )

        if query.provider_name and query.provider_name.strip():
            stmt = stmt.where(
                ProviderModel.name.ilike(f"%{query.provider_name.strip()}%")
            )

        if query.min_price_cents is not None:
            stmt = stmt.where(ProductModel.price_list_cents >= query.min_price_cents)

        if query.max_price_cents is not None:
            stmt = stmt.where(ProductModel.price_list_cents <= query.max_price_cents)

        stmt = stmt.order_by(ProductModel.id.asc())
        if query.offset is not None and query.offset > 0:
            stmt = stmt.offset(query.offset)
        effective_limit = query.limit if (query.limit is not None and query.limit > 0) else 50
        stmt = stmt.limit(effective_limit)

        result = await self._session.scalars(stmt)
        models = result.unique().all()
        return [ProductMapper.to_detail_domain(model) for model in models]
