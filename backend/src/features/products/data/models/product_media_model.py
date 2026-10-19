from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.features.products.data.models.product_model import ProductModel


class ProductMediaModel(Base):
    __tablename__ = "media_products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("products.id"),
        nullable=False,
    )
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[ProductModel] = relationship(
        "ProductModel",
        back_populates="media",
    )
