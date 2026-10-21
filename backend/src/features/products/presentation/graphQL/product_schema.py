import strawberry
from sqlalchemy import func, select

from src.core.db.session import AsyncSessionLocal
from src.features.products.data.models.product_model import ProductModel
from src.features.products.data.repositories.category_repository_adapter import (
    CategoryRepositoryAdapter,
)
from src.features.products.data.repositories.product_repository_adapter import (
    ProductRepositoryAdapter,
)
from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import (
    ProductQuery as ProductQueryEntity,
)
from src.features.products.domain.usecases.category_find_all_usecase import (
    CategoryFindAllUseCase,
)
from src.features.products.domain.usecases.product_find_all_usecase import (
    ProductFindAllUseCase,
)
from src.features.products.domain.usecases.product_find_by_id_usecase import (
    ProductFindByIdUseCase,
)
from src.features.products.domain.usecases.product_find_by_query_usecase import (
    ProductFindByQueryUseCase,
)
from src.features.products.presentation.graphQL.category_schema import CategoryType
from src.features.products.presentation.graphQL.product_media_schema import (
    ProductMediaType,
)
from src.features.providers.presentation.graphQL.provider_schema import ProviderType


@strawberry.type
class ProductDetailType:
    id: str
    name: str
    description: str
    price_list_cents: int
    category: CategoryType
    provider: ProviderType
    media: list[ProductMediaType]

    @strawberry.field
    def images(self) -> list[str]:
        return [m.url for m in self.media]

    @strawberry.field
    def main_image(self) -> str | None:
        for m in self.media:
            if m.is_main:
                return m.url
        return self.media[0].url if self.media else None

    @staticmethod
    def from_domain(entity: ProductDetail) -> "ProductDetailType":
        return ProductDetailType(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            price_list_cents=entity.price_list_cents,
            category=CategoryType.from_domain(entity.category),
            provider=ProviderType.from_domain(entity.provider),
            media=[ProductMediaType.from_domain(item) for item in entity.media],
        )


@strawberry.input
class ProductQueryInput:
    name: str | None = None
    description: str | None = None
    category_name: str | None = None
    provider_name: str | None = None
    min_price_cents: int | None = None
    max_price_cents: int | None = None
    limit: int | None = 50
    offset: int | None = 0

    def to_domain(self) -> ProductQueryEntity:
        return ProductQueryEntity(
            name=self.name,
            description=self.description,
            category_name=self.category_name,
            provider_name=self.provider_name,
            min_price_cents=self.min_price_cents,
            max_price_cents=self.max_price_cents,
            limit=self.limit,
            offset=self.offset,
        )


@strawberry.type
class ProductQuery:
    @strawberry.field
    async def products(
        self,
        limit: int | None = 50,
        offset: int | None = 0,
    ) -> list[ProductDetailType]:
        async with AsyncSessionLocal() as session:
            use_case = ProductFindAllUseCase(ProductRepositoryAdapter(session))
            entities = await use_case.execute(limit=limit, offset=offset)
            return [ProductDetailType.from_domain(entity) for entity in entities]

    @strawberry.field
    async def products_count(self) -> int:
        async with AsyncSessionLocal() as session:
            stmt = select(func.count(ProductModel.id))
            return (await session.execute(stmt)).scalar() or 0

    @strawberry.field
    async def product(self, product_id: str) -> ProductDetailType | None:
        async with AsyncSessionLocal() as session:
            use_case = ProductFindByIdUseCase(ProductRepositoryAdapter(session))
            entity = await use_case.execute(product_id)
            if entity is None:
                return None
            return ProductDetailType.from_domain(entity)

    @strawberry.field
    async def search_products(
        self,
        query: ProductQueryInput | None = None,
    ) -> list[ProductDetailType]:
        domain_query = query.to_domain() if query is not None else ProductQueryEntity()
        async with AsyncSessionLocal() as session:
            use_case = ProductFindByQueryUseCase(ProductRepositoryAdapter(session))
            entities = await use_case.execute(domain_query)
            return [ProductDetailType.from_domain(entity) for entity in entities]

    @strawberry.field
    async def categories(self) -> list[CategoryType]:
        async with AsyncSessionLocal() as session:
            use_case = CategoryFindAllUseCase(CategoryRepositoryAdapter(session))
            entities = await use_case.execute()
            return [CategoryType.from_domain(entity) for entity in entities]
