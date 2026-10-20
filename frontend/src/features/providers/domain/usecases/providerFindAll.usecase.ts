import type { ProviderEntity } from '../entities/provider.entity'
import type { ProviderRepository } from '../repositories/provider.repository'

export class ProviderFindAllUseCase {
  private readonly repository: ProviderRepository

  constructor(repository: ProviderRepository) {
    this.repository = repository
  }

  async execute(): Promise<ProviderEntity[]> {
    return this.repository.findAll()
  }
}
