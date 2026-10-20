import type { SaleEntity } from '../entities/sale.entity'
import type { SaleRepository } from '../repositories/sale.repository'

export class GetSalesUseCase {
  private readonly repository: SaleRepository

  constructor(repository: SaleRepository) {
    this.repository = repository
  }

  async execute(): Promise<SaleEntity[]> {
    return this.repository.getSales()
  }
}
