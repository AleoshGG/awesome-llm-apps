import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strawberry
from src.core.db.session import AsyncSessionLocal, async_engine
from src.features.products.data.repositories.product_repository_adapter import (
    ProductRepositoryAdapter,
)
from src.features.products.domain.entities.category_entity import Category
from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_media_entity import ProductMedia
from src.features.products.domain.repositories.product_repository import ProductRepository
from src.features.products.domain.usecases.product_find_all_usecase import (
    ProductFindAllUseCase,
)
from src.features.products.presentation.graphQL.product_schema import ProductQuery
from src.features.providers.domain.entities.provider_entity import Provider


class ProductPaginationUseCaseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.mock_repo = AsyncMock(spec=ProductRepository)
        self.use_case = ProductFindAllUseCase(self.mock_repo)

    async def test_find_all_delegates_none_by_default(self) -> None:
        self.mock_repo.find_all.return_value = []
        result = await self.use_case.execute()

        self.assertEqual(result, [])
        self.mock_repo.find_all.assert_awaited_once_with(limit=None, offset=None)

    async def test_find_all_passes_limit_and_offset(self) -> None:
        dummy_product = ProductDetail(
            id="prod-1",
            name="Test Product",
            description="Test Desc",
            price_list_cents=1000,
            category=Category(id="cat-1", name="Cat 1"),
            provider=Provider(id="prov-1", name="Prov 1", address="Addr", logo_url="https://logo"),
            media=[ProductMedia(id="m-1", url="https://img1", product_id="prod-1", is_main=True)],
        )
        self.mock_repo.find_all.return_value = [dummy_product]

        result = await self.use_case.execute(limit=10, offset=20)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "prod-1")
        self.mock_repo.find_all.assert_awaited_once_with(limit=10, offset=20)

    async def test_find_all_rejects_negative_limit(self) -> None:
        with self.assertRaises(ValueError):
            await self.use_case.execute(limit=-1)
        self.mock_repo.find_all.assert_not_awaited()

    async def test_find_all_rejects_negative_offset(self) -> None:
        with self.assertRaises(ValueError):
            await self.use_case.execute(offset=-5)
        self.mock_repo.find_all.assert_not_awaited()


class ProductPaginationIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        await async_engine.dispose()

    async def test_repository_pagination_and_deterministic_order(self) -> None:
        async with AsyncSessionLocal() as session:
            repo = ProductRepositoryAdapter(session)
            page1 = await repo.find_all(limit=5, offset=0)
            page2 = await repo.find_all(limit=5, offset=5)

            if len(page1) == 5 and len(page2) == 5:
                page1_ids = {p.id for p in page1}
                page2_ids = {p.id for p in page2}
                # No overlap between distinct pages
                self.assertTrue(page1_ids.isdisjoint(page2_ids))

            # Verify that for products with multiple media, is_main=True comes first
            for p in page1 + page2:
                if len(p.media) > 1:
                    self.assertTrue(p.media[0].is_main)

    async def test_graphql_products_pagination_and_images_field(self) -> None:
        schema = strawberry.Schema(query=ProductQuery)
        query = """
        query TestPagination {
            productsCount
            products(limit: 3, offset: 0) {
                id
                name
                images
                mainImage
                media {
                    id
                    url
                    isMain
                }
            }
        }
        """
        result = await schema.execute(query)
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        products = result.data["products"]
        self.assertLessEqual(len(products), 3)

        if products:
            first = products[0]
            self.assertIn("images", first)
            self.assertIn("mainImage", first)
            self.assertEqual(len(first["images"]), len(first["media"]))
            if first["media"]:
                self.assertEqual(first["mainImage"], first["media"][0]["url"])


if __name__ == "__main__":
    unittest.main()
