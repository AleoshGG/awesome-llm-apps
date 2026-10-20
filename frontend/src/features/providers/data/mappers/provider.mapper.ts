import type { ProviderEntity } from '../../domain/entities/provider.entity'
import type { ProviderDto } from '../models/provider.dto'

export const ProviderMapper = {
  toDomain(dto: ProviderDto): ProviderEntity {
    return {
      id: dto.id,
      name: dto.name,
      address: dto.address,
      logoUrl: dto.logoUrl,
    }
  },
  toDto(entity: ProviderEntity): ProviderDto {
    return {
      id: entity.id,
      name: entity.name,
      address: entity.address,
      logoUrl: entity.logoUrl,
    }
  },
}
