from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.features.products.data.models.product_model import ProductModel
    from src.features.sales.data.models.sale_model import SaleModel


class SaleItemModel(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity_positive"),
    )

    sale_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("sales.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("products.id"),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    sale: Mapped[SaleModel] = relationship("SaleModel", back_populates="items")
    product: Mapped[ProductModel] = relationship("ProductModel")
