import type { SalesAgentRepository } from '../repositories/salesAgent.repository'

export class ConnectSalesAgentUseCase {
  private readonly repository: SalesAgentRepository

  constructor(repository: SalesAgentRepository) {
    this.repository = repository
  }

  async execute(): Promise<void> {
    await this.repository.connect()
  }
}
