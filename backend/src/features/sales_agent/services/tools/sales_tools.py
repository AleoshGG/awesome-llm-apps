from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.sales.domain.exceptions import ProductNotFoundError
from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition
from src.features.sales_agent.domain.exceptions import InvalidToolArgumentsError
from src.features.sales_agent.domain.tools.agent_tool import AgentTool
from src.features.sales_agent.services.mappers.agent_payload_mapper import to_payload


class UseCase(Protocol):
    async def execute(self, **kwargs): ...


UseCaseProvider = Callable[[], AbstractAsyncContextManager[UseCase]]
NonEmptyString = Annotated[str, Field(min_length=1, max_length=500)]
Price = Annotated[int, Field(ge=0)]


class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class SearchArguments(NoArguments):
    name: NonEmptyString | None = None
    description: NonEmptyString | None = None
    category_name: NonEmptyString | None = None
    provider_name: NonEmptyString | None = None
    min_price_cents: Price | None = None
    max_price_cents: Price | None = None

    @model_validator(mode="after")
    def price_range(self):
        if (self.min_price_cents is not None and self.max_price_cents is not None
                and self.min_price_cents > self.max_price_cents):
            raise ValueError("min_price_cents must not exceed max_price_cents")
        return self


class ProductArguments(NoArguments):
    product_id: NonEmptyString


class AddArguments(ProductArguments):
    quantity: Annotated[int, Field(gt=0)]


class CheckoutArguments(NoArguments):
    confirmed: bool = Field(description="True solo tras confirmación explícita del cliente.")

    @model_validator(mode="after")
    def explicit_confirmation(self):
        if not self.confirmed:
            raise ValueError("Se requiere confirmación del cliente")
        return self


class UseCaseTool(AgentTool):
    name: str
    description: str
    result_key: str
    arguments: type[BaseModel] = NoArguments

    def __init__(self, provider: UseCaseProvider) -> None:
        self._provider = provider

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(self.name, self.description, self.arguments.model_json_schema())

    def usecase_arguments(self, args: dict) -> dict:
        return args

    async def execute(self, args: dict) -> dict:
        try:
            validated = self.arguments.model_validate(args).model_dump()
        except ValidationError as exc:
            fields = ", ".join(".".join(map(str, error["loc"])) or "arguments"
                               for error in exc.errors())
            raise InvalidToolArgumentsError(f"Argumentos inválidos: {fields}") from None
        async with self._provider() as usecase:
            result = await usecase.execute(**self.usecase_arguments(validated))
        if result is None:
            raise ProductNotFoundError("Producto no encontrado")
        return {self.result_key: to_payload(result)}


class SearchProductsTool(UseCaseTool):
    name = "search_products"
    description = "Busca productos por texto, categoría, proveedor y rango de precio en centavos."
    result_key = "products"
    arguments = SearchArguments

    def usecase_arguments(self, args: dict) -> dict:
        return {"query": ProductQuery(**args)}


class GetProductDetailsTool(UseCaseTool):
    name = "get_product_details"
    description = "Consulta los detalles actuales de un producto por su identificador."
    result_key = "product"
    arguments = ProductArguments


class ListCategoriesTool(UseCaseTool):
    name = "list_categories"
    description = "Lista las categorías del catálogo."
    result_key = "categories"


class ListProvidersTool(UseCaseTool):
    name = "list_providers"
    description = "Lista los proveedores del catálogo."
    result_key = "providers"


class AddToCartTool(UseCaseTool):
    name = "add_to_cart"
    description = "Agrega unidades al carrito. Si el producto ya existe, suma la cantidad."
    result_key = "cart"
    arguments = AddArguments
    uses_cart = True


class RemoveFromCartTool(UseCaseTool):
    name = "remove_from_cart"
    description = "Elimina del carrito toda la línea del producto indicado."
    result_key = "cart"
    arguments = ProductArguments
    uses_cart = True


class GetCartTool(UseCaseTool):
    name = "get_cart"
    description = "Consulta el carrito compartido con cantidades y precios actuales."
    result_key = "cart"
    uses_cart = True


class CheckoutTool(UseCaseTool):
    name = "checkout"
    description = "Registra la venta y vacía el carrito tras confirmación explícita. No cobra dinero."
    result_key = "sale"
    arguments = CheckoutArguments
    uses_cart = True

    def usecase_arguments(self, args: dict) -> dict:
        return {}
