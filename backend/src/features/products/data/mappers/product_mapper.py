from src.features.products.data.mappers.category_mapper import CategoryMapper
from src.features.products.data.mappers.product_media_mapper import ProductMediaMapper
from src.features.products.data.models.product_model import ProductModel
from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_entity import Product
from src.features.providers.data.mappers.provider_mapper import ProviderMapper


class ProductMapper:
    @staticmethod
    def to_domain(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            price_list_cents=model.price_list_cents,
            provider_id=model.provider_id,
            category_id=model.category_id,
        )

    @staticmethod
    def to_detail_domain(model: ProductModel) -> ProductDetail:
        return ProductDetail(
            id=model.id,
            name=model.name,
            description=model.description,
            price_list_cents=model.price_list_cents,
            category=CategoryMapper.to_domain(model.category),
            provider=ProviderMapper.to_domain(model.provider),
            media=[ProductMediaMapper.to_domain(m) for m in model.media],
        )

    @staticmethod
    def to_model(entity: Product) -> ProductModel:
        return ProductModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            price_list_cents=entity.price_list_cents,
            provider_id=entity.provider_id,
            category_id=entity.category_id,
        )
