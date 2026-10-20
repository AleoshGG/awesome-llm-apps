import type { CartItemEntity } from '../entities/cartItem.entity'
import type { CartRepository } from '../repositories/cart.repository'

export class AddProductToCartUseCase {
  private readonly repository: CartRepository

  constructor(repository: CartRepository) {
    this.repository = repository
  }

  async execute(productId: string, quantity = 1): Promise<CartItemEntity[]> {
    return this.repository.addProduct(productId, quantity)
  }
}
