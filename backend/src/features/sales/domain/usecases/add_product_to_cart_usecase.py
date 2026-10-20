from src.features.products.domain.repositories.product_repository import ProductRepository
from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales.domain.exceptions import (
    InvalidQuantityError,
    ProductNotFoundError,
)
from src.features.sales.domain.repositories.cart_repository import CartRepository


class AddProductToCartUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        product_repository: ProductRepository,
    ) -> None:
        self._cart_repository = cart_repository
        self._product_repository = product_repository

    async def execute(self, product_id: str, quantity: int) -> list[CartItem]:
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be greater than zero")
        if await self._product_repository.find_by_id(product_id) is None:
            raise ProductNotFoundError(f"Product '{product_id}' was not found")
        return await self._cart_repository.add(product_id, quantity)
