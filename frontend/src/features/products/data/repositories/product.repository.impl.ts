import { GRAPHQL_OPERATIONS_DOC } from '../../../../core/config/graphqlSchema.doc'
import { graphqlRequest } from '../../../../core/network/graphqlClient'
import type { ProductDetailEntity } from '../../domain/entities/productDetail.entity'
import type { ProductQueryEntity } from '../../domain/entities/productQuery.entity'
import type { ProductRepository } from '../../domain/repositories/product.repository'
import { ProductMapper } from '../mappers/product.mapper'
import type {
  ProductDetailDto,
  ProductQueryInputDto,
} from '../models/product.dto'

interface GetProductsResponse {
  products: ProductDetailDto[]
}

interface GetProductByIdResponse {
  product: ProductDetailDto | null
}

interface SearchProductsResponse {
  searchProducts: ProductDetailDto[]
}

export class ProductRepositoryImpl implements ProductRepository {
  async findAll(limit?: number, offset?: number): Promise<ProductDetailEntity[]> {
    const data = await graphqlRequest<
      GetProductsResponse,
      { limit?: number; offset?: number }
    >(GRAPHQL_OPERATIONS_DOC.queries.GET_PRODUCTS, { limit, offset })
    return data.products.map(ProductMapper.toDomain)
  }

  async findById(productId: string): Promise<ProductDetailEntity | null> {
    const data = await graphqlRequest<
      GetProductByIdResponse,
      { productId: string }
    >(GRAPHQL_OPERATIONS_DOC.queries.GET_PRODUCT_BY_ID, { productId })

    return data.product ? ProductMapper.toDomain(data.product) : null
  }

  async findByQuery(
    query: ProductQueryEntity,
    signal?: AbortSignal,
  ): Promise<ProductDetailEntity[]> {
    const queryDto: ProductQueryInputDto = ProductMapper.queryToDto(query)
    const data = await graphqlRequest<
      SearchProductsResponse,
      { query: ProductQueryInputDto }
    >(GRAPHQL_OPERATIONS_DOC.queries.SEARCH_PRODUCTS, { query: queryDto }, signal)

    return data.searchProducts.map(ProductMapper.toDomain)
  }

  async count(): Promise<number> {
    const data = await graphqlRequest<{ productsCount: number }>(
      GRAPHQL_OPERATIONS_DOC.queries.GET_PRODUCTS_COUNT,
    )
    return data.productsCount
  }
}
