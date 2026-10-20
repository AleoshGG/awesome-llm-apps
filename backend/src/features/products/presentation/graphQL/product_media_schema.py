import strawberry

from src.features.products.domain.entities.product_media_entity import ProductMedia


@strawberry.type
class ProductMediaType:
    id: str
    url: str
    product_id: str
    is_main: bool

    @staticmethod
    def from_domain(entity: ProductMedia) -> "ProductMediaType":
        return ProductMediaType(
            id=entity.id,
            url=entity.url,
            product_id=entity.product_id,
            is_main=entity.is_main,
        )
