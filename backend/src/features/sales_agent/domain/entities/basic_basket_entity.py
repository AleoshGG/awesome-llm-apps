from dataclasses import dataclass

from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.sales.domain.entities.cart_item_entity import CartItem


@dataclass(frozen=True)
class BasicBasketMatch:
    requested_item: str
    requested_label: str
    requested_quantity: str
    product: ProductDetail
    desired_quantity: int
    match_type: str
    reason: str


@dataclass(frozen=True)
class BasicBasketMissing:
    requested_item: str
    requested_label: str
    requested_quantity: str


@dataclass(frozen=True)
class BasicBasketPlan:
    matches: list[BasicBasketMatch]
    missing: list[BasicBasketMissing]


@dataclass(frozen=True)
class BasicBasketAppliedMatch:
    requested_item: str
    requested_label: str
    requested_quantity: str
    product_id: str
    product_name: str
    desired_quantity: int
    previous_quantity: int
    added_quantity: int
    match_type: str
    reason: str


@dataclass(frozen=True)
class BasicBasketCoverage:
    matched: int
    requested: int


@dataclass(frozen=True)
class BasicBasketResult:
    cart: list[CartItem]
    matched: list[BasicBasketAppliedMatch]
    missing: list[BasicBasketMissing]
    coverage: BasicBasketCoverage
