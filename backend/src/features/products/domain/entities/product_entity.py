from dataclasses import dataclass

@dataclass(frozen=True)
class Product:
    id: str
    name: str
    description: str
    price_list_cents: int
    provider_id: str
    category_id: str
