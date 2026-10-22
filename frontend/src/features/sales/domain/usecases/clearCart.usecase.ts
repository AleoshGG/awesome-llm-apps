import type { CartItemEntity } from '../entities/cartItem.entity'
import type { CartRepository } from '../repositories/cart.repository'

export class ClearCartUseCase {
  private readonly repository: CartRepository

  constructor(repository: CartRepository) {
    this.repository = repository
  }

  async execute(): Promise<CartItemEntity[]> {
    return this.repository.clearCart()
  }
}
