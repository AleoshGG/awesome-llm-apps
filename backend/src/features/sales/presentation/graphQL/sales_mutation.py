from contextlib import nullcontext

import strawberry
from strawberry.types import Info

from src.core.db.session import AsyncSessionLocal
from src.features.products.data.repositories.product_repository_adapter import (
    ProductRepositoryAdapter,
)
from src.features.sales.data.repositories.cart_repository_adapter import (
    CartRepositoryAdapter,
)
from src.features.sales.data.repositories.sale_repository_adapter import (
    SaleRepositoryAdapter,
)
from src.features.sales.domain.usecases.add_product_to_cart_usecase import (
    AddProductToCartUseCase,
)
from src.features.sales.domain.usecases.clear_cart_usecase import ClearCartUseCase
from src.features.sales.domain.usecases.register_sale_usecase import RegisterSaleUseCase
from src.features.sales.domain.usecases.remove_product_from_cart_usecase import (
    RemoveProductFromCartUseCase,
)
from src.features.sales.presentation.graphQL.sales_schema import CartItemType, SaleType


def _cart_lock(info: Info):
    request = info.context.get("request") if isinstance(info.context, dict) else None
    lock = getattr(getattr(request, "app", None), "state", None)
    cart_lock = getattr(lock, "sales_agent_cart_lock", None)
    return cart_lock if cart_lock is not None else nullcontext()


@strawberry.type
class SalesMutation:
    @strawberry.mutation
    async def add_product_to_cart(
        self,
        info: Info,
        product_id: str,
        quantity: int = 1,
    ) -> list[CartItemType]:
        async with _cart_lock(info):
            async with AsyncSessionLocal() as session:
                use_case = AddProductToCartUseCase(
                    CartRepositoryAdapter(session),
                    ProductRepositoryAdapter(session),
                )
                entities = await use_case.execute(
                    product_id=product_id,
                    quantity=quantity,
                )
                return [CartItemType.from_domain(entity) for entity in entities]

    @strawberry.mutation
    async def remove_product_from_cart(
        self,
        info: Info,
        product_id: str,
    ) -> list[CartItemType]:
        async with _cart_lock(info):
            async with AsyncSessionLocal() as session:
                use_case = RemoveProductFromCartUseCase(CartRepositoryAdapter(session))
                entities = await use_case.execute(product_id=product_id)
                return [CartItemType.from_domain(entity) for entity in entities]

    @strawberry.mutation
    async def clear_cart(self, info: Info) -> list[CartItemType]:
        async with _cart_lock(info):
            async with AsyncSessionLocal() as session:
                use_case = ClearCartUseCase(CartRepositoryAdapter(session))
                entities = await use_case.execute()
                return [CartItemType.from_domain(entity) for entity in entities]

    @strawberry.mutation
    async def register_sale(self, info: Info) -> SaleType:
        async with _cart_lock(info):
            async with AsyncSessionLocal() as session:
                use_case = RegisterSaleUseCase(SaleRepositoryAdapter(session))
                entity = await use_case.execute()
                return SaleType.from_domain(entity)
