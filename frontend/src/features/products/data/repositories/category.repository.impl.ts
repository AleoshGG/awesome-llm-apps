import { GRAPHQL_OPERATIONS_DOC } from '../../../../core/config/graphqlSchema.doc'
import { graphqlRequest } from '../../../../core/network/graphqlClient'
import type { CategoryEntity } from '../../domain/entities/category.entity'
import type { CategoryRepository } from '../../domain/repositories/category.repository'
import { CategoryMapper } from '../mappers/product.mapper'
import type { CategoryDto } from '../models/product.dto'

interface GetCategoriesResponse {
  categories: CategoryDto[]
}

export class CategoryRepositoryImpl implements CategoryRepository {
  async findAll(): Promise<CategoryEntity[]> {
    const data = await graphqlRequest<GetCategoriesResponse>(
      GRAPHQL_OPERATIONS_DOC.queries.GET_CATEGORIES,
    )
    return data.categories.map(CategoryMapper.toDomain)
  }
}
