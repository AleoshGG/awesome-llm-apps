import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter

from src.core.db.session import async_engine
from src.features.products.presentation.graphQL.product_schema import ProductQuery
from src.features.providers.presentation.graphQL.provider_schema import ProviderQuery
from src.features.sales.presentation.graphQL.sales_mutation import SalesMutation
from src.features.sales.presentation.graphQL.sales_schema import SalesQuery
from src.features.sales_agent.presentation.sales_agent_router import router as sales_agent_router


@strawberry.type
class Query(ProductQuery, ProviderQuery, SalesQuery):
    pass


@strawberry.type
class Mutation(SalesMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # shortcut: this lock covers one process; use a database lock before scaling workers.
    app.state.sales_agent_cart_lock = asyncio.Lock()
    try:
        yield
    finally:
        await async_engine.dispose()


app = FastAPI(title="Live AI Sales Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales_agent_router)
app.include_router(graphql_router, prefix="/graphql")
