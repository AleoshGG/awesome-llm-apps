import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductQueryEntity } from '../entities/productQuery.entity'
import type { ProductRepository } from '../repositories/product.repository'

export class ProductFindByQueryUseCase {
  private readonly repository: ProductRepository

  constructor(repository: ProductRepository) {
    this.repository = repository
  }

  async execute(
    query: ProductQueryEntity,
    signal?: AbortSignal,
  ): Promise<ProductDetailEntity[]> {
    return this.repository.findByQuery(query, signal)
  }
}
