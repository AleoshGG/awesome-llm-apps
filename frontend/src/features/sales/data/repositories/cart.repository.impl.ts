import { GRAPHQL_OPERATIONS_DOC } from '../../../../core/config/graphqlSchema.doc'
import { graphqlRequest } from '../../../../core/network/graphqlClient'
import type { CartItemEntity } from '../../domain/entities/cartItem.entity'
import type { CartRepository } from '../../domain/repositories/cart.repository'
import { CartMapper } from '../mappers/sales.mapper'
import type { CartItemDto } from '../models/sales.dto'

interface GetCartResponse {
  cart: CartItemDto[]
}

interface AddProductToCartResponse {
  addProductToCart: CartItemDto[]
}

interface RemoveProductFromCartResponse {
  removeProductFromCart: CartItemDto[]
}

export class CartRepositoryImpl implements CartRepository {
  async getCart(): Promise<CartItemEntity[]> {
    const data = await graphqlRequest<GetCartResponse>(
      GRAPHQL_OPERATIONS_DOC.queries.GET_CART,
    )
    return data.cart.map(CartMapper.toDomain)
  }

  async addProduct(
    productId: string,
    quantity = 1,
  ): Promise<CartItemEntity[]> {
    const data = await graphqlRequest<
      AddProductToCartResponse,
      { productId: string; quantity: number }
    >(GRAPHQL_OPERATIONS_DOC.mutations.ADD_PRODUCT_TO_CART, {
      productId,
      quantity,
    })
    return data.addProductToCart.map(CartMapper.toDomain)
  }

  async removeProduct(productId: string): Promise<CartItemEntity[]> {
    const data = await graphqlRequest<
      RemoveProductFromCartResponse,
      { productId: string }
    >(GRAPHQL_OPERATIONS_DOC.mutations.REMOVE_PRODUCT_FROM_CART, { productId })
    return data.removeProductFromCart.map(CartMapper.toDomain)
  }
}
