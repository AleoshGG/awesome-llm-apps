from src.features.products.data.models.category_model import CategoryModel
from src.features.products.domain.entities.category_entity import Category


class CategoryMapper:
    @staticmethod
    def to_domain(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
        )

    @staticmethod
    def to_model(entity: Category) -> CategoryModel:
        return CategoryModel(
            id=entity.id,
            name=entity.name,
        )
