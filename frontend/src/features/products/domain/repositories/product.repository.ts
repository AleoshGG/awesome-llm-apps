import type { ProductDetailEntity } from '../entities/productDetail.entity'
import type { ProductQueryEntity } from '../entities/productQuery.entity'

export interface ProductRepository {
  findAll(): Promise<ProductDetailEntity[]>
  findById(productId: string): Promise<ProductDetailEntity | null>
  findByQuery(query: ProductQueryEntity): Promise<ProductDetailEntity[]>
}
