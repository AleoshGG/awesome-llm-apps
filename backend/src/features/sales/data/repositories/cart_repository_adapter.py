from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.features.products.data.models.product_model import ProductModel
from src.features.sales.data.mappers.cart_item_mapper import CartItemMapper
from src.features.sales.data.models.cart_item_model import CartItemModel
from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales.domain.repositories.cart_repository import CartRepository


class CartRepositoryAdapter(CartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, product_id: str, quantity: int) -> list[CartItem]:
        stmt = insert(CartItemModel).values(
            product_id=product_id,
            quantity=quantity,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[CartItemModel.product_id],
            set_={"quantity": CartItemModel.quantity + quantity},
        )
        try:
            await self._session.execute(stmt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return await self.find_all()

    async def ensure_minimum_quantities(
        self, quantities: dict[str, int]
    ) -> list[CartItem]:
        if not quantities:
            return await self.find_all()
        stmt = insert(CartItemModel).values([
            {"product_id": product_id, "quantity": quantity}
            for product_id, quantity in quantities.items()
        ])
        stmt = stmt.on_conflict_do_update(
            index_elements=[CartItemModel.product_id],
            set_={
                "quantity": func.greatest(
                    CartItemModel.quantity,
                    stmt.excluded.quantity,
                )
            },
        )
        try:
            await self._session.execute(stmt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return await self.find_all()

    async def remove(self, product_id: str) -> list[CartItem]:
        try:
            await self._session.execute(
                delete(CartItemModel).where(CartItemModel.product_id == product_id)
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return await self.find_all()

    async def clear(self) -> list[CartItem]:
        try:
            await self._session.execute(delete(CartItemModel))
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return []

    async def find_all(self) -> list[CartItem]:
        stmt = (
            select(CartItemModel)
            .options(
                joinedload(CartItemModel.product).joinedload(ProductModel.category),
                joinedload(CartItemModel.product).joinedload(ProductModel.provider),
                joinedload(CartItemModel.product).selectinload(ProductModel.media),
            )
            .order_by(CartItemModel.product_id)
        )
        result = await self._session.scalars(stmt)
        return [CartItemMapper.to_domain(model) for model in result.unique().all()]
