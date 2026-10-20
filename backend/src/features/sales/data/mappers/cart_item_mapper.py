from src.features.products.data.mappers.product_mapper import ProductMapper
from src.features.sales.data.models.cart_item_model import CartItemModel
from src.features.sales.domain.entities.cart_item_entity import CartItem


class CartItemMapper:
    @staticmethod
    def to_domain(model: CartItemModel) -> CartItem:
        return CartItem(
            product=ProductMapper.to_detail_domain(model.product),
            quantity=model.quantity,
        )
