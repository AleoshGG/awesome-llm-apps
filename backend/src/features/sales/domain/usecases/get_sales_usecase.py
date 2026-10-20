from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.repositories.sale_repository import SaleRepository


class GetSalesUseCase:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Sale]:
        return await self._repository.find_all()
