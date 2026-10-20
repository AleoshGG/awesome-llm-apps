import type { SaleEntity } from '../entities/sale.entity'

export interface SaleRepository {
  getSales(): Promise<SaleEntity[]>
  registerSale(): Promise<SaleEntity>
}
