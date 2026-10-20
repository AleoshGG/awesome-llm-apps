import { GRAPHQL_OPERATIONS_DOC } from '../../../../core/config/graphqlSchema.doc'
import { graphqlRequest } from '../../../../core/network/graphqlClient'
import type { ProviderEntity } from '../../domain/entities/provider.entity'
import type { ProviderRepository } from '../../domain/repositories/provider.repository'
import { ProviderMapper } from '../mappers/provider.mapper'
import type { ProviderDto } from '../models/provider.dto'

interface GetProvidersResponse {
  providers: ProviderDto[]
}

export class ProviderRepositoryImpl implements ProviderRepository {
  async findAll(): Promise<ProviderEntity[]> {
    const data = await graphqlRequest<GetProvidersResponse>(
      GRAPHQL_OPERATIONS_DOC.queries.GET_PROVIDERS,
    )
    return data.providers.map(ProviderMapper.toDomain)
  }
}
