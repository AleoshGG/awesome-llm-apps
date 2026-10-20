from src.features.providers.data.models.provider_model import ProviderModel
from src.features.providers.domain.entities.provider_entity import Provider


class ProviderMapper:
    @staticmethod
    def to_domain(model: ProviderModel) -> Provider:
        return Provider(
            id=model.id,
            name=model.name,
            address=model.address,
            logo_url=model.logo_url,
        )

    @staticmethod
    def to_model(entity: Provider) -> ProviderModel:
        return ProviderModel(
            id=entity.id,
            name=entity.name,
            address=entity.address,
            logo_url=entity.logo_url,
        )
