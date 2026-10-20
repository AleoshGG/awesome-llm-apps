import type { ProviderEntity } from '../entities/provider.entity'

export interface ProviderRepository {
  findAll(): Promise<ProviderEntity[]>
}
