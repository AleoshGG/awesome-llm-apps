import type { CategoryEntity } from '../entities/category.entity'
import type { CategoryRepository } from '../repositories/category.repository'

export class CategoryFindAllUseCase {
  private readonly repository: CategoryRepository

  constructor(repository: CategoryRepository) {
    this.repository = repository
  }

  async execute(): Promise<CategoryEntity[]> {
    return this.repository.findAll()
  }
}
