from src.features.providers.domain.entities.provider_entity import Provider
from src.features.providers.domain.repositories.provider_repository import ProviderRepository


class ProviderFindAllUseCase:
    def __init__(self, repository: ProviderRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Provider]:
        return await self._repository.find_all()
