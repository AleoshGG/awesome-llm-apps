import { GRAPHQL_OPERATIONS_DOC } from '../../../../core/config/graphqlSchema.doc'
import { graphqlRequest } from '../../../../core/network/graphqlClient'
import type { SaleEntity } from '../../domain/entities/sale.entity'
import type { SaleRepository } from '../../domain/repositories/sale.repository'
import { SaleMapper } from '../mappers/sales.mapper'
import type { SaleDto } from '../models/sales.dto'

interface GetSalesResponse {
  sales: SaleDto[]
}

interface RegisterSaleResponse {
  registerSale: SaleDto
}

export class SaleRepositoryImpl implements SaleRepository {
  async getSales(): Promise<SaleEntity[]> {
    const data = await graphqlRequest<GetSalesResponse>(
      GRAPHQL_OPERATIONS_DOC.queries.GET_SALES,
    )
    return data.sales.map(SaleMapper.toDomain)
  }

  async registerSale(): Promise<SaleEntity> {
    const data = await graphqlRequest<RegisterSaleResponse>(
      GRAPHQL_OPERATIONS_DOC.mutations.REGISTER_SALE,
    )
    return SaleMapper.toDomain(data.registerSale)
  }
}
