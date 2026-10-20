import type { CartItemEntity } from '../entities/cartItem.entity'
import type { CartRepository } from '../repositories/cart.repository'

export class RemoveProductFromCartUseCase {
  private readonly repository: CartRepository

  constructor(repository: CartRepository) {
    this.repository = repository
  }

  async execute(productId: string): Promise<CartItemEntity[]> {
    return this.repository.removeProduct(productId)
  }
}
