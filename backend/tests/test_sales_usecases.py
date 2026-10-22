import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.products.domain.repositories.product_repository import ProductRepository
from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.exceptions import (
    EmptyCartError,
    InvalidQuantityError,
    ProductNotFoundError,
)
from src.features.sales.domain.repositories.cart_repository import CartRepository
from src.features.sales.domain.repositories.sale_repository import SaleRepository
from src.features.sales.domain.usecases.add_product_to_cart_usecase import (
    AddProductToCartUseCase,
)
from src.features.sales.domain.usecases.clear_cart_usecase import ClearCartUseCase
from src.features.sales.domain.usecases.get_cart_usecase import GetCartUseCase
from src.features.sales.domain.usecases.get_sales_usecase import GetSalesUseCase
from src.features.sales.domain.usecases.register_sale_usecase import RegisterSaleUseCase
from src.features.sales.domain.usecases.remove_product_from_cart_usecase import (
    RemoveProductFromCartUseCase,
)


class SalesUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.cart_repository = AsyncMock(spec=CartRepository)
        self.product_repository = AsyncMock(spec=ProductRepository)
        self.sale_repository = AsyncMock(spec=SaleRepository)

    async def test_add_product_rejects_non_positive_quantity(self) -> None:
        usecase = AddProductToCartUseCase(
            self.cart_repository,
            self.product_repository,
        )

        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                with self.assertRaises(InvalidQuantityError):
                    await usecase.execute("product-1", quantity)

        self.product_repository.find_by_id.assert_not_awaited()
        self.cart_repository.add.assert_not_awaited()

    async def test_add_product_rejects_unknown_product(self) -> None:
        self.product_repository.find_by_id.return_value = None
        usecase = AddProductToCartUseCase(
            self.cart_repository,
            self.product_repository,
        )

        with self.assertRaises(ProductNotFoundError):
            await usecase.execute("missing", 1)

        self.cart_repository.add.assert_not_awaited()

    async def test_add_product_delegates_valid_item(self) -> None:
        expected = [object()]
        self.product_repository.find_by_id.return_value = object()
        self.cart_repository.add.return_value = expected
        usecase = AddProductToCartUseCase(
            self.cart_repository,
            self.product_repository,
        )

        result = await usecase.execute("product-1", 2)

        self.product_repository.find_by_id.assert_awaited_once_with("product-1")
        self.cart_repository.add.assert_awaited_once_with("product-1", 2)
        self.assertIs(result, expected)

    async def test_get_and_remove_cart_delegate_to_repository(self) -> None:
        expected = [object()]
        self.cart_repository.find_all.return_value = expected
        self.cart_repository.remove.return_value = expected

        self.assertIs(
            await GetCartUseCase(self.cart_repository).execute(),
            expected,
        )
        self.assertIs(
            await RemoveProductFromCartUseCase(self.cart_repository).execute(
                "product-1"
            ),
            expected,
        )
        self.cart_repository.find_all.assert_awaited_once_with()
        self.cart_repository.remove.assert_awaited_once_with("product-1")
        self.cart_repository.clear.return_value = []
        self.assertEqual(await ClearCartUseCase(self.cart_repository).execute(), [])
        self.cart_repository.clear.assert_awaited_once_with()

    async def test_register_sale_returns_repository_result(self) -> None:
        expected = Sale(
            id="sale-1",
            created_at=datetime(2026, 10, 19, tzinfo=UTC),
            items=[],
        )
        self.sale_repository.register.return_value = expected

        result = await RegisterSaleUseCase(self.sale_repository).execute()

        self.assertIs(result, expected)
        self.sale_repository.register.assert_awaited_once_with()

    async def test_register_sale_propagates_empty_cart_error(self) -> None:
        self.sale_repository.register.side_effect = EmptyCartError("empty")

        with self.assertRaises(EmptyCartError):
            await RegisterSaleUseCase(self.sale_repository).execute()

    async def test_get_sales_preserves_repository_order(self) -> None:
        expected = [
            Sale(
                id="newer",
                created_at=datetime(2026, 10, 19, tzinfo=UTC),
                items=[],
            ),
            Sale(
                id="older",
                created_at=datetime(2026, 10, 18, tzinfo=UTC),
                items=[],
            ),
        ]
        self.sale_repository.find_all.return_value = expected

        result = await GetSalesUseCase(self.sale_repository).execute()

        self.assertIs(result, expected)
        self.sale_repository.find_all.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
