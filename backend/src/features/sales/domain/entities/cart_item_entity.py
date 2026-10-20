from dataclasses import dataclass

from src.features.products.domain.entities.product_detail_entity import ProductDetail


@dataclass(frozen=True)
class CartItem:
    product: ProductDetail
    quantity: int
