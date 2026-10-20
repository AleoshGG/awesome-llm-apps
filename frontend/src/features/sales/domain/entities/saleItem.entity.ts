import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'

/**
 * Entidad pura de dominio que representa un artículo dentro de una venta cerrada.
 */
export interface SaleItemEntity {
  product: ProductDetailEntity
  quantity: number
}
