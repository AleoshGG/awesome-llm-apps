import re
import unicodedata
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from src.features.products.domain.entities.product_detail_entity import ProductDetail
from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.sales.domain.entities.cart_item_entity import CartItem
from src.features.sales_agent.domain.entities.basic_basket_entity import (
    BasicBasketMatch,
    BasicBasketMissing,
    BasicBasketPlan,
)


class UseCase(Protocol):
    async def execute(self, **kwargs): ...


UseCaseProvider = Callable[[], AbstractAsyncContextManager[UseCase]]


@dataclass(frozen=True)
class BasicBasketSpec:
    key: str
    label: str
    quantity: str
    queries: tuple[str, ...]
    target: Decimal
    unit: str
    reject: tuple[str, ...] = ()


BASIC_BASKET = (
    BasicBasketSpec("corn_tortilla", "Tortilla de maíz", "4 kg", ("tortilla de maíz",), Decimal(4000), "g", ("harina", "tiritas")),
    BasicBasketSpec("rice", "Arroz en grano", "1 kg", ("arroz",), Decimal(1000), "g"),
    BasicBasketSpec("black_beans", "Frijol negro", "900 g", ("frijol negro",), Decimal(900), "g"),
    BasicBasketSpec("white_bread", "Pan blanco de caja", "680 g", ("pan blanco",), Decimal(680), "g"),
    BasicBasketSpec("soup_pasta", "Pasta para sopa", "220 g", ("pasta para sopa",), Decimal(220), "g"),
    BasicBasketSpec("vegetable_oil", "Aceite vegetal comestible", "946 ml", ("aceite vegetal", "aceite canola"), Decimal(946), "ml"),
    BasicBasketSpec("standard_sugar", "Azúcar estándar", "1 kg", ("azúcar estándar",), Decimal(1000), "g"),
    BasicBasketSpec("flaked_tuna", "Atún en hojuelas", "2 latas de 140 g", ("atún en hojuelas",), Decimal(2), "piece"),
    BasicBasketSpec("tomato_sardines", "Sardina en tomate", "1 lata de 425 g", ("sardina",), Decimal(1), "piece"),
    BasicBasketSpec("cow_milk", "Leche de vaca", "5 litros", ("leche entera", "leche de vaca", "leche"), Decimal(5000), "ml", ("sabor", "deslactosada", "evaporada", "condensada")),
    BasicBasketSpec("chicken_eggs", "Huevo de gallina", "18 piezas", ("huevo",), Decimal(18), "piece"),
    BasicBasketSpec("chicken_meat", "Carne de pollo", "1 kg", ("carne de pollo",), Decimal(1000), "g", ("sopa", "consome")),
    BasicBasketSpec("beef", "Carne de res", "1 kg", ("carne de res",), Decimal(1000), "g", ("sopa", "consome")),
    BasicBasketSpec("pork", "Carne de cerdo", "1 kg", ("carne de cerdo",), Decimal(1000), "g", ("sopa", "consome")),
    BasicBasketSpec("tomato", "Jitomate saladet", "1 kg", ("jitomate saladet", "jitomate"), Decimal(1000), "g", ("pure", "salsa")),
    BasicBasketSpec("white_onion", "Cebolla blanca", "1 kg", ("cebolla blanca",), Decimal(1000), "g", ("morada", "amarilla", "rabo")),
    BasicBasketSpec("jalapeno", "Chile jalapeño", "1 kg", ("chile jalapeño",), Decimal(1000), "g", ("serrano", "poblano", "habanero", "arbol")),
    BasicBasketSpec("white_potato", "Papa blanca", "1 kg", ("papa blanca",), Decimal(1000), "g", ("frita", "pure", "cambray")),
    BasicBasketSpec("carrot", "Zanahoria", "1 kg", ("zanahoria",), Decimal(1000), "g", ("baby", "rallada")),
    BasicBasketSpec("lime", "Limón", "1 kg", ("limón",), Decimal(1000), "g"),
    BasicBasketSpec("apple", "Manzana", "1 kg", ("manzana",), Decimal(1000), "g"),
    BasicBasketSpec("banana", "Plátano", "1 kg", ("plátano",), Decimal(1000), "g", ("macho", "dominico")),
    BasicBasketSpec("bar_soap", "Jabón de tocador", "1 pieza", ("jabón de tocador",), Decimal(1), "piece", ("liquido", "shampoo")),
    BasicBasketSpec("toilet_paper", "Papel higiénico", "1 bolsa de 4 piezas", ("papel higiénico",), Decimal(4), "piece", ("servilleta", "toalla")),
)


def _normal(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _package_amount(name: str, unit: str) -> Decimal | None:
    value = _normal(name)
    if unit == "piece":
        match = re.search(r"(?:x\s*)?(\d+)\s*(?:piezas?|pzas?|rollos?|huevos?)", value)
        return Decimal(match.group(1)) if match else Decimal(1)
    pattern = r"(\d+(?:[.,]\d+)?)\s*(kg|g|l|lt|litros?|ml)\b"
    matches = re.findall(pattern, value)
    if not matches:
        return Decimal(1000) if "por kg" in value or value.endswith(" kg") else None
    number, source = matches[-1]
    amount = Decimal(number.replace(",", "."))
    if source == "kg":
        amount *= 1000
    elif source in {"l", "lt", "litro", "litros"}:
        amount *= 1000
    if unit == "g" and source in {"ml", "l", "lt", "litro", "litros"}:
        return None
    if unit == "ml" and source in {"g", "kg"}:
        return None
    return amount


class DeterministicBasicBasketService:
    def __init__(self, product_provider: UseCaseProvider) -> None:
        self._product_provider = product_provider

    async def plan(self, cart: list[CartItem]) -> BasicBasketPlan:
        terms = tuple(dict.fromkeys(query for spec in BASIC_BASKET for query in spec.queries))
        async with self._product_provider() as usecase:
            products = await usecase.execute(query=ProductQuery(terms=terms, limit=500))
        by_id = {product.id: product for product in products}
        by_id.update({item.product.id: item.product for item in cart})
        used: set[str] = set()
        matches: list[BasicBasketMatch] = []
        missing: list[BasicBasketMissing] = []
        for spec in BASIC_BASKET:
            ranked = [
                (self._score(spec, product), product)
                for product in by_id.values()
                if product.id not in used and self._score(spec, product) is not None
            ]
            if not ranked:
                missing.append(BasicBasketMissing(spec.key, spec.label, spec.quantity))
                continue
            score, product = min(ranked, key=lambda entry: (entry[0], entry[1].id))
            package = _package_amount(product.name, spec.unit) or spec.target
            desired = max(1, int((spec.target / package).to_integral_value(rounding="ROUND_CEILING")))
            used.add(product.id)
            matches.append(BasicBasketMatch(
                spec.key, spec.label, spec.quantity, product, desired,
                "exact" if score[0] == 0 and package == spec.target else "nearby",
                f"Presentación de {product.name} seleccionada por coincidencia de catálogo.",
            ))
        return BasicBasketPlan(matches=matches, missing=missing)

    @staticmethod
    def _score(spec: BasicBasketSpec, product: ProductDetail) -> tuple | None:
        name = _normal(product.name)
        searchable = _normal(f"{product.name} {product.description}")
        queries = [_normal(query) for query in spec.queries]
        if not any(query in searchable for query in queries):
            return None
        if any(term in name for term in spec.reject):
            return None
        package = _package_amount(product.name, spec.unit)
        distance = abs(package - spec.target) if package is not None else spec.target
        name_rank = 0 if any(query in name for query in queries) else 1
        package_count = max(1, int((spec.target / package).to_integral_value(rounding="ROUND_CEILING"))) if package else 99
        return name_rank, distance, package_count, product.price_list_cents
