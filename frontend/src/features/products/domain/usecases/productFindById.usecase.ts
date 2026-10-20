import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductRepository } from '../repositories/product.repository'

export class ProductFindByIdUseCase {
  private readonly repository: ProductRepository

  constructor(repository: ProductRepository) {
    this.repository = repository
  }

  async execute(productId: string): Promise<ProductDetailEntity | null> {
    return this.repository.findById(productId)
  }
}
