import type { ProductRepository } from '../repositories/product.repository'

export class ProductCountUseCase {
  private readonly repository: ProductRepository

  constructor(repository: ProductRepository) {
    this.repository = repository
  }

  async execute(): Promise<number> {
    return this.repository.count()
  }
}
