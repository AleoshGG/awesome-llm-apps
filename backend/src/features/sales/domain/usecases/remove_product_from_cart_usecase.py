from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales.domain.repositories.cart_repository import CartRepository


class RemoveProductFromCartUseCase:
    def __init__(self, repository: CartRepository) -> None:
        self._repository = repository

    async def execute(self, product_id: str) -> list[CartItem]:
        return await self._repository.remove(product_id)
