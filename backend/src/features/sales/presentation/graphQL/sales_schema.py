from datetime import datetime

import strawberry

from src.core.db.session import AsyncSessionLocal
from src.features.products.presentation.graphQL.product_schema import ProductDetailType
from src.features.sales.data.repositories.cart_repository_adapter import (
    CartRepositoryAdapter,
)
from src.features.sales.data.repositories.sale_repository_adapter import (
    SaleRepositoryAdapter,
)
from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.entities.sale_item_entity import SaleItem
from src.features.sales.domain.usecases.get_cart_usecase import GetCartUseCase
from src.features.sales.domain.usecases.get_sales_usecase import GetSalesUseCase


@strawberry.type
class CartItemType:
    product: ProductDetailType
    quantity: int

    @staticmethod
    def from_domain(entity: CartItem) -> "CartItemType":
        return CartItemType(
            product=ProductDetailType.from_domain(entity.product),
            quantity=entity.quantity,
        )


@strawberry.type
class SaleItemType:
    product: ProductDetailType
    quantity: int

    @staticmethod
    def from_domain(entity: SaleItem) -> "SaleItemType":
        return SaleItemType(
            product=ProductDetailType.from_domain(entity.product),
            quantity=entity.quantity,
        )


@strawberry.type
class SaleType:
    id: str
    created_at: datetime
    items: list[SaleItemType]

    @staticmethod
    def from_domain(entity: Sale) -> "SaleType":
        return SaleType(
            id=entity.id,
            created_at=entity.created_at,
            items=[SaleItemType.from_domain(item) for item in entity.items],
        )


@strawberry.type
class SalesQuery:
    @strawberry.field
    async def cart(self) -> list[CartItemType]:
        async with AsyncSessionLocal() as session:
            use_case = GetCartUseCase(CartRepositoryAdapter(session))
            entities = await use_case.execute()
            return [CartItemType.from_domain(entity) for entity in entities]

    @strawberry.field
    async def sales(self) -> list[SaleType]:
        async with AsyncSessionLocal() as session:
            use_case = GetSalesUseCase(SaleRepositoryAdapter(session))
            entities = await use_case.execute()
            return [SaleType.from_domain(entity) for entity in entities]
