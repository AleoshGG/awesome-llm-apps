import type { ProductDetailEntity } from '../../../products/domain/entities/productDetail.entity'

/**
 * Entidad pura de dominio que representa una línea en el carrito de compras.
 */
export interface CartItemEntity {
  product: ProductDetailEntity
  quantity: number
}
