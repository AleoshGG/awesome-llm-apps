from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSearchResult:
    summary: str
    observed_features: list[str]
    matched_categories: list[str]
    searches: list[dict]
    products: list[dict]
