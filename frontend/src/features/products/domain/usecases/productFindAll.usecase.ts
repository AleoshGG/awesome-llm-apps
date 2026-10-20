import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductRepository } from '../repositories/product.repository'

export class ProductFindAllUseCase {
  private readonly repository: ProductRepository

  constructor(repository: ProductRepository) {
    this.repository = repository
  }

  async execute(): Promise<ProductDetailEntity[]> {
    return this.repository.findAll()
  }
}
