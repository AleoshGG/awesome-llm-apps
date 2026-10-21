from typing import Protocol

from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales_agent.domain.entities.basic_basket_entity import BasicBasketPlan


class BasicBasketService(Protocol):
    async def plan(self, cart: list[CartItem]) -> BasicBasketPlan: ...
