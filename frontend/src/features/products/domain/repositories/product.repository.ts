import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductQueryEntity } from '../entities/productQuery.entity'

export interface ProductRepository {
  findAll(limit?: number, offset?: number): Promise<ProductDetailEntity[]>
  findById(productId: string): Promise<ProductDetailEntity | null>
  findByQuery(
    query: ProductQueryEntity,
    signal?: AbortSignal,
  ): Promise<ProductDetailEntity[]>
  count(): Promise<number>
}
