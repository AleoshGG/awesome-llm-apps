import strawberry

from src.features.products.domain.entities.category_entity import Category


@strawberry.type
class CategoryType:
    id: str
    name: str

    @staticmethod
    def from_domain(entity: Category) -> "CategoryType":
        return CategoryType(
            id=entity.id,
            name=entity.name,
        )
