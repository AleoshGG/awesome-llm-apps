from dataclasses import dataclass

from src.features.products.domain.entities.category_entity import Category
from src.features.products.domain.entities.product_media_entity import ProductMedia
from src.features.providers.domain.entities.provider_entity import Provider


@dataclass(frozen=True)
class ProductDetail:
    id: str
    name: str
    description: str
    price_list_cents: int
    category: Category
    provider: Provider
    media: list[ProductMedia]
