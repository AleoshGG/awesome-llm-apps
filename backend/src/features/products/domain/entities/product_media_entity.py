from dataclasses import dataclass

@dataclass(frozen=True)
class ProductMedia:
    id: str
    url: str
    product_id: str
    is_main: bool