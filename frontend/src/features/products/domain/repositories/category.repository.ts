import type { CategoryEntity } from '../entities/category.entity'

export interface CategoryRepository {
  findAll(): Promise<CategoryEntity[]>
}
