from src.features.sales.domain.repositories.cart_repository import CartRepository
from src.features.sales_agent.domain.entities.basic_basket_entity import (
    BasicBasketAppliedMatch,
    BasicBasketCoverage,
    BasicBasketResult,
)
from src.features.sales_agent.domain.services.basic_basket_service import BasicBasketService


class BuildBasicBasketUseCase:
    def __init__(
        self,
        cart_repository: CartRepository,
        basket_service: BasicBasketService,
    ) -> None:
        self._cart_repository = cart_repository
        self._basket_service = basket_service

    async def execute(self) -> BasicBasketResult:
        current_cart = await self._cart_repository.find_all()
        plan = await self._basket_service.plan(current_cart)
        previous = {item.product.id: item.quantity for item in current_cart}
        targets = {
            match.product.id: match.desired_quantity
            for match in plan.matches
        }
        cart = await self._cart_repository.ensure_minimum_quantities(targets)
        matched = [
            BasicBasketAppliedMatch(
                requested_item=match.requested_item,
                requested_label=match.requested_label,
                requested_quantity=match.requested_quantity,
                product_id=match.product.id,
                product_name=match.product.name,
                desired_quantity=match.desired_quantity,
                previous_quantity=previous.get(match.product.id, 0),
                added_quantity=max(
                    0,
                    match.desired_quantity - previous.get(match.product.id, 0),
                ),
                match_type=match.match_type,
                reason=match.reason,
            )
            for match in plan.matches
        ]
        return BasicBasketResult(
            cart=cart,
            matched=matched,
            missing=plan.missing,
            coverage=BasicBasketCoverage(
                matched=len(matched),
                requested=len(matched) + len(plan.missing),
            ),
        )
