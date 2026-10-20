from abc import ABC, abstractmethod

from src.features.providers.domain.entities.provider_entity import Provider


class ProviderRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Provider]:
        pass
