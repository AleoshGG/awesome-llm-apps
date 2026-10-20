from src.features.products.data.models.product_media_model import ProductMediaModel
from src.features.products.domain.entities.product_media_entity import ProductMedia


class ProductMediaMapper:
    @staticmethod
    def to_domain(model: ProductMediaModel) -> ProductMedia:
        return ProductMedia(
            id=model.id,
            url=model.url,
            product_id=model.product_id,
            is_main=model.is_main,
        )

    @staticmethod
    def to_model(entity: ProductMedia) -> ProductMediaModel:
        return ProductMediaModel(
            id=entity.id,
            url=entity.url,
            product_id=entity.product_id,
            is_main=entity.is_main,
        )
