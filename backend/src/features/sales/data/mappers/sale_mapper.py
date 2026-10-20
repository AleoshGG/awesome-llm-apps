from src.features.products.data.mappers.product_mapper import ProductMapper
from src.features.sales.data.models.sale_model import SaleModel
from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.entities.sale_item_entity import SaleItem


class SaleMapper:
    @staticmethod
    def to_domain(model: SaleModel) -> Sale:
        return Sale(
            id=model.id,
            created_at=model.created_at,
            items=[
                SaleItem(
                    product=ProductMapper.to_detail_domain(item.product),
                    quantity=item.quantity,
                )
                for item in model.items
            ],
        )
