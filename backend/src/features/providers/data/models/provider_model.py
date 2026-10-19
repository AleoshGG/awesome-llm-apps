from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base

if TYPE_CHECKING:
    from src.features.products.data.models.product_model import ProductModel


class ProviderModel(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    logo_url: Mapped[str] = mapped_column(String, nullable=False)

    products: Mapped[list[ProductModel]] = relationship(
        "ProductModel",
        back_populates="provider",
    )
