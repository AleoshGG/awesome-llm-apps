from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.features.products.data.models.category_model import CategoryModel
    from src.features.products.data.models.product_media_model import ProductMediaModel
    from src.features.providers.data.models.provider_model import ProviderModel


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price_list_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("providers.id"),
        nullable=False,
    )
    category_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("categories.id"),
        nullable=False,
    )

    provider: Mapped[ProviderModel] = relationship(
        "ProviderModel",
        back_populates="products",
    )
    category: Mapped[CategoryModel] = relationship(
        "CategoryModel",
        back_populates="products",
    )
    media: Mapped[list[ProductMediaModel]] = relationship(
        "ProductMediaModel",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(ProductMediaModel.is_main), ProductMediaModel.id",
    )
