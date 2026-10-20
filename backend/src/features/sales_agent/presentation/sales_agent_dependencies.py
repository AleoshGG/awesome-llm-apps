from contextlib import asynccontextmanager

from fastapi import WebSocket

from src.core.db.session import AsyncSessionLocal
from src.core.settings.settings import settings
from src.features.products.data.repositories.category_repository_adapter import CategoryRepositoryAdapter
from src.features.products.data.repositories.product_repository_adapter import ProductRepositoryAdapter
from src.features.products.domain.usecases.category_find_all_usecase import CategoryFindAllUseCase
from src.features.products.domain.usecases.product_find_by_id_usecase import ProductFindByIdUseCase
from src.features.products.domain.usecases.product_find_by_query_usecase import ProductFindByQueryUseCase
from src.features.providers.data.repositories.provider_repository_adapter import ProviderRepositoryAdapter
from src.features.providers.domain.usecases.provider_find_all_usecase import ProviderFindAllUseCase
from src.features.sales.data.repositories.cart_repository_adapter import CartRepositoryAdapter
from src.features.sales.data.repositories.sale_repository_adapter import SaleRepositoryAdapter
from src.features.sales.domain.usecases.add_product_to_cart_usecase import AddProductToCartUseCase
from src.features.sales.domain.usecases.get_cart_usecase import GetCartUseCase
from src.features.sales.domain.usecases.register_sale_usecase import RegisterSaleUseCase
from src.features.sales.domain.usecases.remove_product_from_cart_usecase import RemoveProductFromCartUseCase
from src.features.sales_agent.data.services.gemini_realtime_voice_service_adapter import GeminiRealtimeVoiceServiceAdapter
from src.features.sales_agent.data.services.adk_visual_product_search_service import AdkVisualProductSearchService
from src.features.sales_agent.domain.entities.realtime_session_config_entity import RealtimeSessionConfig
from src.features.sales_agent.domain.prompts.sales_agent_prompt import SYSTEM_INSTRUCTION
from src.features.sales_agent.domain.tools.tool_registry import ToolRegistry
from src.features.sales_agent.domain.usecases.sales_agent_run_session_usecase import SalesAgentRunSessionUseCase
from src.features.sales_agent.services.tools.sales_tools import (
    AddToCartTool, CheckoutTool, GetCartTool, GetProductDetailsTool,
    ListCategoriesTool, ListProvidersTool, RemoveFromCartTool, SearchProductsTool,
)


def usecase_provider(factory):
    @asynccontextmanager
    async def provide():
        async with AsyncSessionLocal() as session:
            yield factory(session)
    return provide


def build_tool_registry() -> ToolRegistry:
    return ToolRegistry([
        SearchProductsTool(usecase_provider(
            lambda session: ProductFindByQueryUseCase(ProductRepositoryAdapter(session))
        )),
        GetProductDetailsTool(usecase_provider(
            lambda session: ProductFindByIdUseCase(ProductRepositoryAdapter(session))
        )),
        ListCategoriesTool(usecase_provider(
            lambda session: CategoryFindAllUseCase(CategoryRepositoryAdapter(session))
        )),
        ListProvidersTool(usecase_provider(
            lambda session: ProviderFindAllUseCase(ProviderRepositoryAdapter(session))
        )),
        AddToCartTool(usecase_provider(lambda session: AddProductToCartUseCase(
            CartRepositoryAdapter(session), ProductRepositoryAdapter(session)
        ))),
        RemoveFromCartTool(usecase_provider(
            lambda session: RemoveProductFromCartUseCase(CartRepositoryAdapter(session))
        )),
        GetCartTool(usecase_provider(
            lambda session: GetCartUseCase(CartRepositoryAdapter(session))
        )),
        CheckoutTool(usecase_provider(
            lambda session: RegisterSaleUseCase(SaleRepositoryAdapter(session))
        )),
    ])


def get_sales_agent(websocket: WebSocket) -> SalesAgentRunSessionUseCase:
    key = settings.GOOGLE_API_KEY
    api_key = key.get_secret_value() if key else None
    return SalesAgentRunSessionUseCase(
        GeminiRealtimeVoiceServiceAdapter(api_key),
        build_tool_registry(),
        RealtimeSessionConfig(
            model=settings.SALES_AGENT_GEMINI_MODEL,
            voice=settings.SALES_AGENT_VOICE,
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[],
        ),
        websocket.app.state.sales_agent_cart_lock,
        visual_search=AdkVisualProductSearchService(
            api_key,
            settings.SALES_AGENT_VISUAL_MODEL,
            usecase_provider(
                lambda session: CategoryFindAllUseCase(CategoryRepositoryAdapter(session))
            ),
            usecase_provider(
                lambda session: ProductFindByQueryUseCase(ProductRepositoryAdapter(session))
            ),
        ),
    )
