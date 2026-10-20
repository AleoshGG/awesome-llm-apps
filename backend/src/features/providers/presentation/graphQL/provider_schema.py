import strawberry

from src.core.db.session import AsyncSessionLocal
from src.features.providers.data.repositories.provider_repository_adapter import (
    ProviderRepositoryAdapter,
)
from src.features.providers.domain.entities.provider_entity import Provider
from src.features.providers.domain.usecases.provider_find_all_usecase import (
    ProviderFindAllUseCase,
)


@strawberry.type
class ProviderType:
    id: str
    name: str
    address: str
    logo_url: str

    @staticmethod
    def from_domain(entity: Provider) -> "ProviderType":
        return ProviderType(
            id=entity.id,
            name=entity.name,
            address=entity.address,
            logo_url=entity.logo_url,
        )


@strawberry.type
class ProviderQuery:
    @strawberry.field
    async def providers(self) -> list[ProviderType]:
        async with AsyncSessionLocal() as session:
            use_case = ProviderFindAllUseCase(ProviderRepositoryAdapter(session))
            entities = await use_case.execute()
            return [ProviderType.from_domain(entity) for entity in entities]
