from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.features.products.data.models.product_model import ProductModel
from src.features.sales.data.mappers.sale_mapper import SaleMapper
from src.features.sales.data.models.cart_item_model import CartItemModel
from src.features.sales.data.models.sale_item_model import SaleItemModel
from src.features.sales.data.models.sale_model import SaleModel
from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.exceptions import EmptyCartError
from src.features.sales.domain.repositories.sale_repository import SaleRepository


class SaleRepositoryAdapter(SaleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _detail_stmt(self):
        return select(SaleModel).options(
            selectinload(SaleModel.items)
            .joinedload(SaleItemModel.product)
            .joinedload(ProductModel.category),
            selectinload(SaleModel.items)
            .joinedload(SaleItemModel.product)
            .joinedload(ProductModel.provider),
            selectinload(SaleModel.items)
            .joinedload(SaleItemModel.product)
            .selectinload(ProductModel.media),
        )

    async def register(self) -> Sale:
        sale_id = str(uuid4())
        try:
            result = await self._session.scalars(
                select(CartItemModel)
                .order_by(CartItemModel.product_id)
                .with_for_update()
            )
            cart_items = result.all()
            if not cart_items:
                raise EmptyCartError("Cannot register a sale from an empty cart")

            sale = SaleModel(
                id=sale_id,
                items=[
                    SaleItemModel(
                        product_id=item.product_id,
                        quantity=item.quantity,
                    )
                    for item in cart_items
                ],
            )
            self._session.add(sale)
            await self._session.execute(delete(CartItemModel))
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        result = await self._session.scalars(
            self._detail_stmt().where(SaleModel.id == sale_id)
        )
        model = result.unique().one()
        return SaleMapper.to_domain(model)

    async def find_all(self) -> list[Sale]:
        stmt = self._detail_stmt().order_by(
            SaleModel.created_at.desc(),
            SaleModel.id.desc(),
        )
        result = await self._session.scalars(stmt)
        return [SaleMapper.to_domain(model) for model in result.unique().all()]
