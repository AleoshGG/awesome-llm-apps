import type { SaleItemEntity } from './saleItem.entity'

/**
 * Entidad pura de dominio que representa una venta registrada en la tienda.
 */
export interface SaleEntity {
  id: string
  createdAt: string
  items: SaleItemEntity[]
}
