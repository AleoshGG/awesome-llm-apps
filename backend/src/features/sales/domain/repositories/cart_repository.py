from abc import ABC, abstractmethod

from src.features.sales.domain.entities.cart_item_entity import CartItem


class CartRepository(ABC):
    @abstractmethod
    async def add(self, product_id: str, quantity: int) -> list[CartItem]:
        pass

    @abstractmethod
    async def remove(self, product_id: str) -> list[CartItem]:
        pass

    @abstractmethod
    async def find_all(self) -> list[CartItem]:
        pass
