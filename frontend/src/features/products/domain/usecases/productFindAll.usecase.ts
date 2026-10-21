import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductRepository } from '../repositories/product.repository'

export class ProductFindAllUseCase {
  private readonly repository: ProductRepository

  constructor(repository: ProductRepository) {
    this.repository = repository
  }

  async execute(limit?: number, offset?: number): Promise<ProductDetailEntity[]> {
    return this.repository.findAll(limit, offset)
  }
}
