from dataclasses import dataclass
from datetime import datetime

from src.features.sales.domain.entities.sale_item_entity import SaleItem


@dataclass(frozen=True)
class Sale:
    id: str
    created_at: datetime
    items: list[SaleItem]
