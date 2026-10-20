from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.providers.data.mappers.provider_mapper import ProviderMapper
from src.features.providers.data.models.provider_model import ProviderModel
from src.features.providers.domain.entities.provider_entity import Provider
from src.features.providers.domain.repositories.provider_repository import ProviderRepository


class ProviderRepositoryAdapter(ProviderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Provider]:
        stmt = select(ProviderModel)
        result = await self._session.scalars(stmt)
        models = result.all()
        return [ProviderMapper.to_domain(model) for model in models]
