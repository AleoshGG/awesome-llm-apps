from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.features.sales.data.models.sale_item_model import SaleItemModel


class SaleModel(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("ix_sales_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list[SaleItemModel]] = relationship(
        "SaleItemModel",
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItemModel.product_id",
    )
