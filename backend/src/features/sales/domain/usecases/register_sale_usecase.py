from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.repositories.sale_repository import SaleRepository


class RegisterSaleUseCase:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    async def execute(self) -> Sale:
        return await self._repository.register()
