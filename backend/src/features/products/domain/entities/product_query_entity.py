from dataclasses import dataclass


@dataclass(frozen=True)
class ProductQuery:
    name: str | None = None
    description: str | None = None
    category_name: str | None = None
    provider_name: str | None = None
    min_price_cents: int | None = None
    max_price_cents: int | None = None
    limit: int | None = 50
    offset: int | None = 0
