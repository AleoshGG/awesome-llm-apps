import sys
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.products.domain.entities.category_entity import Category
from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.providers.domain.entities.provider_entity import Provider
from src.features.sales.data.repositories.cart_repository_adapter import CartRepositoryAdapter
from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales.domain.repositories.cart_repository import CartRepository
from src.features.sales_agent.data.services.deterministic_basic_basket_service import (
    BASIC_BASKET,
    DeterministicBasicBasketService,
)
from src.features.sales_agent.domain.entities.basic_basket_entity import (
    BasicBasketAppliedMatch,
    BasicBasketCoverage,
    BasicBasketMatch,
    BasicBasketMissing,
    BasicBasketPlan,
    BasicBasketResult,
)
from src.features.sales_agent.domain.services.basic_basket_service import BasicBasketService
from src.features.sales_agent.domain.usecases.build_basic_basket_usecase import (
    BuildBasicBasketUseCase,
)
from src.features.sales_agent.services.tools.sales_tools import BuildBasicBasketTool


def product(product_id: str, name: str, price: int = 1000) -> ProductDetail:
    return ProductDetail(
        id=product_id,
        name=name,
        description=name,
        price_list_cents=price,
        category=Category("c1", "Abarrotes"),
        provider=Provider("v1", "Tienda", "México", "https://example.test/logo"),
        media=[],
    )


class BasicBasketServiceTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def provider(usecase):
        @asynccontextmanager
        async def provide():
            yield usecase
        return provide

    async def test_selects_real_candidates_with_one_catalog_query(self):
        rice = product("rice-1", "Arroz Super Extra 900g")

        async def execute(*, query):
            return [rice] if "arroz" in query.terms else []

        usecase = SimpleNamespace(execute=AsyncMock(side_effect=execute))
        plan = await DeterministicBasicBasketService(self.provider(usecase)).plan([])
        self.assertEqual([match.product.id for match in plan.matches], ["rice-1"])
        self.assertEqual(len(plan.missing), 23)
        usecase.execute.assert_awaited_once()
        query = usecase.execute.await_args.kwargs["query"]
        self.assertEqual(query.limit, 500)
        self.assertIn("arroz", query.terms)

    async def test_rejects_wrong_variant_and_computes_package_quantity(self):
        wrong = product("milk-flavor", "Leche sabor chocolate 1 L", 500)
        milk = product("milk", "Leche Entera Lala 1 L", 2000)
        usecase = SimpleNamespace(execute=AsyncMock(return_value=[wrong, milk]))
        plan = await DeterministicBasicBasketService(self.provider(usecase)).plan([])
        match = next(item for item in plan.matches if item.requested_item == "cow_milk")
        self.assertEqual(match.product.id, "milk")
        self.assertEqual(match.desired_quantity, 5)

    async def test_reuses_a_matching_cart_product(self):
        rice = product("rice-cart", "Arroz 1 kg")
        usecase = SimpleNamespace(execute=AsyncMock(return_value=[]))
        plan = await DeterministicBasicBasketService(self.provider(usecase)).plan([
            CartItem(rice, 1)
        ])
        self.assertEqual(plan.matches[0].product.id, "rice-cart")
        self.assertEqual(len(BASIC_BASKET), 24)


class BuildBasicBasketUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_completes_only_missing_quantities_and_preserves_report(self):
        rice = product("rice-1", "Arroz 900g")
        tuna = product("tuna-1", "Atún en Hojuelas 130g")
        unrelated = product("other-1", "Café")
        current = [CartItem(rice, 1), CartItem(tuna, 1), CartItem(unrelated, 2)]
        updated = [CartItem(rice, 1), CartItem(tuna, 2), CartItem(unrelated, 2)]
        repository = AsyncMock(spec=CartRepository)
        repository.find_all.return_value = current
        repository.ensure_minimum_quantities.return_value = updated
        service = AsyncMock(spec=BasicBasketService)
        service.plan.return_value = BasicBasketPlan(matches=[
            BasicBasketMatch("rice", "Arroz", "1 kg", rice, 1, "nearby", "900 g"),
            BasicBasketMatch("flaked_tuna", "Atún", "2 latas", tuna, 2, "nearby", "130 g"),
        ], missing=[BasicBasketMissing("cow_milk", "Leche", "5 litros")])

        result = await BuildBasicBasketUseCase(repository, service).execute()

        repository.ensure_minimum_quantities.assert_awaited_once_with({
            "rice-1": 1, "tuna-1": 2,
        })
        self.assertEqual([item.added_quantity for item in result.matched], [0, 1])
        self.assertEqual((result.coverage.matched, result.coverage.requested), (2, 3))
        self.assertIs(result.cart, updated)

    async def test_tool_exposes_cart_and_basket_report(self):
        usecase = AsyncMock()
        usecase.execute.return_value = BasicBasketResult(
            cart=["cart"],
            matched=[BasicBasketAppliedMatch(
                "rice", "Arroz", "1 kg", "rice-1", "Arroz 900g",
                1, 0, 1, "nearby", "Presentación de 900 g",
            )],
            missing=[],
            coverage=BasicBasketCoverage(matched=1, requested=24),
        )

        @asynccontextmanager
        async def provider():
            yield usecase

        result = await BuildBasicBasketTool(provider).execute({})
        self.assertEqual(result["cart"], ["cart"])
        self.assertEqual(result["basket"]["coverage"], {"matched": 1, "requested": 24})

    async def test_planning_failure_never_writes_cart(self):
        repository = AsyncMock(spec=CartRepository)
        repository.find_all.return_value = []
        service = AsyncMock(spec=BasicBasketService)
        service.plan.side_effect = RuntimeError("model failed")
        with self.assertRaisesRegex(RuntimeError, "model failed"):
            await BuildBasicBasketUseCase(repository, service).execute()
        repository.ensure_minimum_quantities.assert_not_awaited()


class CartRepositoryBulkTests(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_quantities_commits_one_statement(self):
        session = AsyncMock()
        scalar_result = MagicMock()
        scalar_result.unique.return_value.all.return_value = []
        session.scalars.return_value = scalar_result
        result = await CartRepositoryAdapter(session).ensure_minimum_quantities({
            "rice-1": 1, "tuna-1": 2,
        })
        self.assertEqual(result, [])
        session.execute.assert_awaited_once()
        self.assertIn("greatest", str(session.execute.await_args.args[0]).lower())
        session.commit.assert_awaited_once()

    async def test_ensure_quantities_rolls_back_on_failure(self):
        session = AsyncMock()
        session.execute.side_effect = RuntimeError("db failed")
        with self.assertRaisesRegex(RuntimeError, "db failed"):
            await CartRepositoryAdapter(session).ensure_minimum_quantities({"rice-1": 1})
        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
